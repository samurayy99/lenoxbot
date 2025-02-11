from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from utils.logger import BotLogger
from utils.helpers import Helpers


class PositionManager:
    """
    Verwaltet Trading-Positionen mit Persistenz und dynamischen Updates.
    """

    def __init__(self, logger: BotLogger, positions_file: str = "data/positions.json"):
        """
        Initialisiert den Position Manager.

        Args:
            logger: Logger-Instanz
            positions_file: JSON-Datei für offene Positionen
        """
        self.logger = logger
        self.helpers = Helpers()
        self.positions_file = positions_file
        self.active_positions: Dict[str, Any] = self._load_positions()

    def _load_positions(self) -> Dict[str, Any]:
        """
        Lädt Positionen aus der JSON-Datei.

        Returns:
            Positionen als Dictionary
        """
        try:
            with open(self.positions_file, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            self.logger.warning(f"{self.positions_file} nicht gefunden. Erstelle eine leere Datei.")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Fehler beim Laden von Positionen: {str(e)}")
            return {}

    def _save_positions(self) -> None:
        """
        Speichert Positionen in die JSON-Datei.
        """
        try:
            with open(self.positions_file, "w") as file:
                json.dump(self.active_positions, file, indent=4)
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Positionen: {str(e)}")

    def open_position(self, token: str, entry_price: float, amount: float,
                      stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> str:
        """
        Öffnet eine neue Position.

        Args:
            token: Token-Adresse
            entry_price: Einstiegspreis
            amount: Handelsmenge
            stop_loss: Optional - Stop Loss Preis
            take_profit: Optional - Take Profit Preis

        Returns:
            Position ID
        """
        position_id = f"{token}_{datetime.now().timestamp()}"
        position = {
            "token": token,
            "entry_price": entry_price,
            "amount": amount,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "status": "open",
            "entry_time": self.helpers.get_current_timestamp(),
            "last_update": self.helpers.get_current_timestamp(),
            "realized_pnl": 0.0
        }

        self.active_positions[position_id] = position
        self._save_positions()
        self.logger.info(f"Neue Position eröffnet: {position_id}")
        return position_id

    def close_position(self, position_id: str, exit_price: float) -> Optional[Dict[str, Any]]:
        """
        Schließt eine bestehende Position.

        Args:
            position_id: Position ID
            exit_price: Ausstiegspreis

        Returns:
            Abgeschlossene Position oder None
        """
        position = self.active_positions.get(position_id)
        if not position or position["status"] != "open":
            self.logger.warning(f"Position nicht gefunden oder bereits geschlossen: {position_id}")
            return None

        position["exit_price"] = exit_price
        position["exit_time"] = self.helpers.get_current_timestamp()
        position["status"] = "closed"
        position["realized_pnl"] = self._calculate_pnl(position, exit_price)

        self._save_positions()
        self.logger.info(f"Position geschlossen: {position_id} mit PnL: {position['realized_pnl']}")
        return position

    def update_position(self, position_id: str, current_price: float,
                        stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> bool:
        """
        Aktualisiert eine bestehende Position.

        Args:
            position_id: Position ID
            current_price: Aktueller Preis
            stop_loss: Optional - Neuer Stop Loss
            take_profit: Optional - Neuer Take Profit

        Returns:
            True wenn erfolgreich
        """
        position = self.active_positions.get(position_id)
        if not position or position["status"] != "open":
            self.logger.warning(f"Position nicht gefunden oder geschlossen: {position_id}")
            return False

        if stop_loss is not None:
            position["stop_loss"] = stop_loss
        if take_profit is not None:
            position["take_profit"] = take_profit

        position["last_update"] = self.helpers.get_current_timestamp()
        self._save_positions()
        self.logger.info(f"Position aktualisiert: {position_id}")
        return True

    def _calculate_pnl(self, position: Dict[str, Any], current_price: float) -> float:
        """
        Berechnet den PnL einer Position.

        Args:
            position: Positionsdetails
            current_price: Aktueller Preis

        Returns:
            Realisierter Gewinn/Verlust
        """
        entry_price = position["entry_price"]
        return round((current_price - entry_price) * position["amount"], 2)

    def get_active_positions(self) -> List[Dict[str, Any]]:
        """
        Gibt alle aktiven Positionen zurück.

        Returns:
            Liste offener Positionen
        """
        return [pos for pos in self.active_positions.values() if pos["status"] == "open"]

    def clear_positions(self) -> None:
        """
        Löscht alle Positionen.
        """
        self.active_positions = {}
        self._save_positions()
        self.logger.info("Alle Positionen gelöscht.")

    def check_position_exits(self, current_price: float) -> List[str]:
        """
        Prüft ob Positionen geschlossen werden sollen.
        
        Args:
            current_price: Aktueller Token-Preis
            
        Returns:
            Liste von Position-IDs die geschlossen werden sollen
        """
        exits = []
        for pos_id, position in self.active_positions.items():
            if (position["stop_loss"] and current_price <= position["stop_loss"]) or \
               (position["take_profit"] and current_price >= position["take_profit"]):
                exits.append(pos_id)
        return exits
