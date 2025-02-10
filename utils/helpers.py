import json
import time
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from typing import Any, Dict, Callable

class Helpers:
    """
    Utility-Funktionen für den Trading-Bot
    """

    @staticmethod
    def format_amount(amount: float, decimals: int = 8) -> str:
        """
        Formatiert einen Betrag mit der korrekten Anzahl von Dezimalstellen.
        """
        return str(Decimal(str(amount)).quantize(Decimal('0.' + '0' * decimals), rounding=ROUND_DOWN))

    @staticmethod
    def safe_divide(a: float, b: float, default: float = 0.0) -> float:
        """
        Sichere Division mit Standardwert bei Division durch 0.
        """
        try:
            return a / b if b != 0 else default
        except Exception:
            return default

    @staticmethod
    def retry(func: Callable, retries: int = 3, delay: float = 1.0, *args, **kwargs) -> Any:
        """
        Wiederholt eine Funktion bei Fehlern.
        """
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise e

    @staticmethod
    def load_json(filepath: str) -> Dict[str, Any]:
        """
        Lädt JSON-Daten aus einer Datei sicher.
        """
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            raise ValueError(f"Fehler beim Laden von {filepath}: {e}")

    @staticmethod
    def save_json(filepath: str, data: Dict[str, Any]) -> None:
        """
        Speichert Daten als JSON in einer Datei.
        """
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def get_current_timestamp() -> str:
        """
        Gibt den aktuellen Zeitstempel im ISO-Format zurück.
        """
        return datetime.now().isoformat()

    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float, default: float = 0.0) -> float:
        """
        Berechnet die prozentuale Änderung zwischen zwei Werten.
        """
        if old_value == 0:
            return default  # Wenn der alte Wert 0 ist, kann kein Prozentsatz berechnet werden.
        return Helpers.safe_divide(new_value - old_value, old_value) * 100
