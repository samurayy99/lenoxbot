import logging
import os
from datetime import datetime
from typing import Optional

class Logger:
    """
    Zentralisiertes Logging-System für den Trading-Bot.
    Unterstützt tagesbasierte Logs und Trade-spezifisches Logging.
    """
    
    def __init__(self, log_dir: str = "logs", log_level: int = logging.INFO):
        """
        Initialisiert den Logger.
        
        Args:
            log_dir: Verzeichnis für Log-Dateien.
            log_level: Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        """
        self.log_dir = log_dir
        self.logger = logging.getLogger("TradingBot")
        self.logger.setLevel(log_level)
        
        # Verzeichnis erstellen, falls es nicht existiert
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Handlers hinzufügen
        self._setup_file_handler()
        self._setup_console_handler()

    def _setup_file_handler(self) -> None:
        """Konfiguriert den Datei-Handler mit Tages-Log-Dateien."""
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = f"{self.log_dir}/trading_bot_{date_str}.log"
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(file_handler)

    def _setup_console_handler(self) -> None:
        """Konfiguriert den Console-Handler."""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)

    def _get_formatter(self) -> logging.Formatter:
        """Erstellt ein einheitliches Log-Format."""
        return logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def trade_log(self, action: str, token: str, amount: float, price: Optional[float] = None) -> None:
        """
        Spezielles Logging für Handelsaktionen.
        
        Args:
            action: Typ der Aktion (buy, sell, etc.).
            token: Token-Symbol oder Adresse.
            amount: Handelsmenge.
            price: Optional - Preis des Trades.
        """
        price_info = f" at {price}" if price else ""
        self.logger.info(f"TRADE - {action.upper()}: {amount} {token}{price_info}")

    def debug(self, message: str) -> None:
        """Debug-Level Log."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Info-Level Log."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Warning-Level Log."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Error-Level Log."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Critical-Level Log."""
        self.logger.critical(message)

    def exception(self, message: str) -> None:
        """Exception-Level Log mit Stacktrace."""
        self.logger.exception(message)
