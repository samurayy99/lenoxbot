from typing import Dict, Any
from utils.logger import BotLogger
from utils.helpers import Helpers


class RiskManager:
    """
    Verwaltet Risiko-Parameter, Positionsgrößen und Handelsstatistiken.
    """

    def __init__(self, logger: BotLogger, config: Dict[str, Any]):
        """
        Initialisiert den Risk Manager.

        Args:
            logger: Logger-Instanz
            config: Trading-Konfiguration mit Risiko-Parametern
        """
        self.logger = logger
        self.helpers = Helpers()
        self.config = config
        self.daily_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "last_reset": self.helpers.get_current_timestamp()
        }

    def validate_trade(self, current_budget: float, active_trades: int, trade_amount: float) -> bool:
        """
        Überprüft, ob ein neuer Trade den Risikomanagement-Regeln entspricht.

        Args:
            current_budget: Verfügbares Budget
            active_trades: Aktuelle offene Trades
            trade_amount: Betrag des neuen Trades

        Returns:
            True, wenn der Trade erlaubt ist, sonst False.
        """
        if active_trades >= self.config["max_active_trades"]:
            self.logger.warning("Maximale Anzahl aktiver Trades erreicht.")
            return False

        if trade_amount > self.config["max_position_size"]:
            self.logger.warning(f"Trade-Betrag überschreitet maximale Positionsgröße: {trade_amount}")
            return False

        if current_budget < trade_amount:
            self.logger.warning(f"Unzureichendes Budget: {current_budget} < {trade_amount}")
            return False

        return True

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """
        Berechnet die optimale Positionsgröße basierend auf Risiko.

        Args:
            entry_price: Einstiegspreis
            stop_loss: Stop Loss Preis

        Returns:
            Optimale Positionsgröße
        """
        try:
            risk_per_trade = self.config["account_size"] * (self.config["risk_per_trade"] / 100)
            risk_per_unit = abs(entry_price - stop_loss)

            if risk_per_unit == 0:
                return 0

            position_size = risk_per_trade / risk_per_unit
            return min(position_size, self.config["max_position_size"] / entry_price)

        except Exception as e:
            self.logger.error(f"Fehler bei Positionsgrößen-Berechnung: {str(e)}")
            return 0

    def check_stop_loss(self, position: Dict[str, Any], current_price: float) -> bool:
        """
        Überprüft, ob die Stop Loss-Grenze erreicht wurde.

        Args:
            position: Positionsdetails
            current_price: Aktueller Preis des Tokens

        Returns:
            True, wenn Stop Loss erreicht, sonst False.
        """
        stop_loss = position.get("stop_loss")
        if stop_loss and current_price <= stop_loss:
            self.logger.info(f"Stop Loss erreicht für {position['token']}. Preis: {current_price}")
            return True
        return False

    def check_take_profit(self, position: Dict[str, Any], current_price: float) -> bool:
        """
        Überprüft, ob die Take Profit-Grenze erreicht wurde.

        Args:
            position: Positionsdetails
            current_price: Aktueller Preis des Tokens

        Returns:
            True, wenn Take Profit erreicht, sonst False.
        """
        take_profit = position.get("take_profit")
        if take_profit and current_price >= take_profit:
            self.logger.info(f"Take Profit erreicht für {position['token']}. Preis: {current_price}")
            return True
        return False

    def update_trade_stats(self, pnl: float) -> None:
        """
        Aktualisiert die Trading-Statistiken.

        Args:
            pnl: Gewinn/Verlust des Trades
        """
        self.daily_stats["total_trades"] += 1
        self.daily_stats["total_pnl"] += pnl

        if pnl > 0:
            self.daily_stats["winning_trades"] += 1
        else:
            self.daily_stats["losing_trades"] += 1

        # Aktualisiere Drawdown
        if pnl < 0:
            current_drawdown = self.daily_stats["total_pnl"]
            self.daily_stats["max_drawdown"] = min(self.daily_stats["max_drawdown"], current_drawdown)

        self.logger.info(f"Trading-Statistiken aktualisiert. PnL: {pnl}")

    def reset_daily_stats(self) -> None:
        """
        Setzt die täglichen Statistiken zurück.
        """
        self.daily_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "last_reset": self.helpers.get_current_timestamp()
        }
        self.logger.info("Tägliche Statistiken zurückgesetzt.")

    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Gibt aktuelle Risiko-Metriken zurück.

        Returns:
            Dictionary mit Risiko-Metriken
        """
        total_trades = self.daily_stats["total_trades"]
        win_rate = (self.daily_stats["winning_trades"] / total_trades) * 100 if total_trades > 0 else 0

        return {
            "win_rate": round(win_rate, 2),
            "total_pnl": round(self.daily_stats["total_pnl"], 2),
            "max_drawdown": round(self.daily_stats["max_drawdown"], 2),
            "total_trades": total_trades,
            "risk_per_trade": self.config["risk_per_trade"],
            "account_size": self.config["account_size"]
        }

    def check_trade_allowed(self, token: str, liquidity: float, price: float) -> bool:
        """
        Prüft ob ein Trade den Risikoparametern entspricht.
        """
        min_liquidity = self.config.get("min_liquidity", 10000)
        if liquidity < min_liquidity:
            self.logger.warning(f"Zu geringe Liquidität: {liquidity} < {min_liquidity}")
            return False
        return True

    def get_stop_loss(self, entry_price: float) -> float:
        """
        Berechnet den Stop Loss Preis.
        """
        stop_loss_percent = self.config.get("stop_loss_percent", 0.05)
        return entry_price * (1 - stop_loss_percent)

    def get_take_profit(self, entry_price: float) -> float:
        """
        Berechnet den Take Profit Preis.
        """
        take_profit_percent = self.config.get("take_profit_percent", 0.15)
        return entry_price * (1 + take_profit_percent)
