import json
from decimal import Decimal
from datetime import datetime
from enum import Enum
from pathlib import Path
from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


def _append_file(filename: str, obj) -> int:
    """Добавляет объект obj в файл filename в формате JSON (по одной строке на объект)."""
    def custom_serializer(o):
        if isinstance(o, Decimal):
            return str(o)  # сохраняем как строку, чтобы избежать float-ошибок
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        raise TypeError(f"Type {type(o)} not serializable")

    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj.__dict__, default=custom_serializer) + '\n')

    with open(filename, 'r', encoding='utf-8') as f:
        return len(f.readlines())


def _read_file(filename: str) -> list[dict]:
    if not Path(filename).exists():
        return []
    with open(filename, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f.readlines()]


def _write_file(filename: str, objects: list[dict]):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        for obj in objects:
            f.write(json.dumps(obj, default=str) + '\n')


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = Path(root_directory_path)

    # Задание 1. Сохранение моделей
    def add_model(self, model: Model) -> Model:
        file_path = self.root_directory_path / "models.json"
        _append_file(file_path, model)
        return model

    # Задание 1. Сохранение автомобилей
    def add_car(self, car: Car) -> Car:
        file_path = self.root_directory_path / "cars.json"
        _append_file(file_path, car)
        return car

    # Задание 2. Сохранение продаж
    def sell_car(self, sale: Sale) -> Car:
        cars_file = self.root_directory_path / "cars.json"
        sales_file = self.root_directory_path / "sales.json"

        cars = _read_file(cars_file)
        for c in cars:
            if c["vin"] == sale.car_vin:
                c["status"] = CarStatus.sold.value
                _write_file(cars_file, cars)
                _append_file(sales_file, sale)
                return Car(
                    vin=c["vin"],
                    model=c["model"],
                    price=Decimal(c["price"]),
                    date_start=datetime.fromisoformat(c["date_start"]),
                    status=CarStatus(c["status"])
                )
        raise ValueError(f"Car with VIN {sale.car_vin} not found")

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        cars_file = self.root_directory_path / "cars.json"
        cars = _read_file(cars_file)
        return [
            Car(
                vin=c["vin"],
                model=c["model"],
                price=Decimal(c["price"]),
                date_start=datetime.fromisoformat(c["date_start"]),
                status=CarStatus(c["status"])
            )
            for c in cars if c["status"] == status.value
        ]

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        cars_file = self.root_directory_path / "cars.json"
        sales_file = self.root_directory_path / "sales.json"
        models_file = self.root_directory_path / "models.json"

        cars = _read_file(cars_file)
        sales = _read_file(sales_file)
        models = {m["id"]: m for m in _read_file(models_file)}

        car = next((c for c in cars if c["vin"] == vin), None)
        if not car:
            return None

        model = models.get(car["model"])
        sale = next((s for s in sales if s["car_vin"] == vin), None)

        return CarFullInfo(
            vin=car["vin"],
            car_model_name=model["name"] if model else "",
            car_model_brand=model["brand"] if model else "",
            price=Decimal(car["price"]),
            date_start=datetime.fromisoformat(car["date_start"]),
            status=CarStatus(car["status"]),
            sales_date=datetime.fromisoformat(sale["sales_date"]) if sale else None,
            sales_cost=Decimal(sale["cost"]) if sale else None,
        )

    # Задание 5. Обновление VIN
    def update_vin(self, vin: str, new_vin: str) -> Car:
        cars_file = self.root_directory_path / "cars.json"
        cars = _read_file(cars_file)
        for c in cars:
            if c["vin"] == vin:
                c["vin"] = new_vin
                _write_file(cars_file, cars)
                return Car(
                    vin=c["vin"],
                    model=c["model"],
                    price=Decimal(c["price"]),
                    date_start=datetime.fromisoformat(c["date_start"]),
                    status=CarStatus(c["status"])
                )
        raise ValueError(f"Car with VIN {vin} not found")

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        cars_file = self.root_directory_path / "cars.json"
        sales_file = self.root_directory_path / "sales.json"

        sales = _read_file(sales_file)
        sale = next((s for s in sales if s["sales_number"] == sales_number), None)
        if not sale:
            raise ValueError(f"Sale with number {sales_number} not found")
        sales.remove(sale)
        _write_file(sales_file, sales)

        cars = _read_file(cars_file)
        for c in cars:
            if c["vin"] == sale["car_vin"]:
                c["status"] = CarStatus.available.value
                _write_file(cars_file, cars)
                return Car(
                    vin=c["vin"],
                    model=c["model"],
                    price=Decimal(c["price"]),
                    date_start=datetime.fromisoformat(c["date_start"]),
                    status=CarStatus(c["status"])
                )
        raise ValueError(f"Car with VIN {sale['car_vin']} not found")

    def top_models_by_sales(self) -> list[ModelSaleStats]:
        sales_file = self.root_directory_path / "sales.json"
        models_file = self.root_directory_path / "models.json"

        sales = _read_file(sales_file)
        models = {m["id"]: m for m in _read_file(models_file)}

        cars = _read_file(self.root_directory_path / "cars.json")
        count_by_model = {}
        for s in sales:
            car = next((c for c in cars if c["vin"] == s["car_vin"]), None)
            if car:
                model_id = car["model"]
                count_by_model[model_id] = count_by_model.get(model_id, 0) + 1

        stats = [
            ModelSaleStats(
                car_model_name=models[m_id]["name"],
                brand=models[m_id]["brand"],
                sales_number=count
            )
            for m_id, count in count_by_model.items()
            if count > 0
        ]
        # сортировка по убыванию продаж
        stats.sort(key=lambda x: x.sales_number, reverse=True)
        return stats[:3]  # берем топ-3