import asyncio
import os
import base58
from utils.config_loader import ConfigLoader
from utils.logger import BotLogger
from services.dexscreener import DexScreener
from services.solana_sniffer import SolanaSniffer
from services.jupiter import Jupiter
from utils.position_manager import PositionManager
from services.risk_management import RiskManager
from services.phantom_wallet import PhantomWallet
from services.sentiment import SentimentAnalyzer

class TradingBot:
    """
    Hauptlogik des Trading-Bots.
    """

    def __init__(self):
        # Initialisierung der Konfigurations- und Logging-Systeme
        self.config = ConfigLoader()
        self.logger = BotLogger()

        # Laden des Private Keys mit Fehlerhandling
        wallet_private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not wallet_private_key:
            raise ValueError("⚠ WALLET_PRIVATE_KEY ist nicht gesetzt! Überprüfe deine .env Datei.")

        # Laden der Module mit korrekten Parametern
        self.dexscreener = DexScreener(self.logger, self.config.get("dexscreener.filters"))
        self.sniffer = SolanaSniffer(self.logger)
        self.jupiter = Jupiter(self.logger)
        self.wallet = PhantomWallet(wallet_private_key)  # Fix: Sicherer Private Key-Check
        self.position_manager = PositionManager(self.logger)
        self.risk_manager = RiskManager(self.logger, self.config.get("trading"))
        self.sentiment_analyzer = SentimentAnalyzer(self.logger)  # Fix: Korrekte Initialisierung

    async def run(self):
        """
        Startet den Trading-Bot.
        """
        self.logger.info("🚀 Trading-Bot gestartet!")
        await self.wallet.connect()

        try:
            while True:
                await self.execute_trading_cycle()
                await asyncio.sleep(self.config.get("trading.cycle_interval", 60))
        except KeyboardInterrupt:
            self.logger.info("❌ Bot gestoppt.")
        finally:
            await self.wallet.disconnect()

    async def execute_trading_cycle(self):
        """
        Führt einen kompletten Trading-Zyklus aus.
        """
        self.logger.info("🔄 Neuer Trading-Zyklus gestartet...")
        opportunities = await self.dexscreener.get_filtered_tokens("solana")  # Fix: Methode korrigiert

        for opportunity in opportunities:
            token_address = opportunity["address"]
            current_price = opportunity["price_usd"]

            # Sicherheitschecks
            if not await self.sniffer.check_contract(token_address):  # Fix: Methode korrigiert
                self.logger.warning(f"⚠ Token nicht sicher: {token_address}")
                continue

            # Sentiment-Check
            sentiment_data = await self.sentiment_analyzer.get_token_sentiment(opportunity["symbol"])  # Fix: Methode korrigiert
            if not self.sentiment_analyzer.is_bullish_sentiment(sentiment_data):
                self.logger.info(f"📉 Sentiment nicht bullish: {opportunity['symbol']}")
                continue

            # Risiko-Prüfung
            if not self.risk_manager.check_trade_allowed(token_address, opportunity["liquidity_usd"], current_price):
                self.logger.warning(f"❌ Trade nicht erlaubt für {opportunity['symbol']}")
                continue

            # Position eröffnen
            position_size = self.risk_manager.calculate_position_size(
                current_price, self.risk_manager.get_stop_loss(current_price)
            )
            if not position_size:
                self.logger.warning(f"⚠ Positionsgröße zu klein für {opportunity['symbol']}")
                continue

            # Trading ausführen
            route = await self.jupiter.get_best_route(token_address, "So11111111111111111111111111111111111111112", float(position_size))
            if not route:
                self.logger.error(f"❌ Keine Route gefunden für {opportunity['symbol']}")
                continue
                
            swap_tx = await self.jupiter.execute_trade(route, base58.b58encode(self.wallet.keypair.to_bytes()).decode("utf-8"))

            if not swap_tx:
                self.logger.error(f"❌ Trade fehlgeschlagen für {opportunity['symbol']}")
                continue

            # Position speichern
            stop_loss = self.risk_manager.get_stop_loss(current_price)
            take_profit = self.risk_manager.get_take_profit(current_price)
            self.position_manager.open_position(token_address, current_price, position_size, stop_loss, take_profit)
            self.logger.info(f"✅ Trade ausgeführt: {opportunity['symbol']} | Größe: {position_size}")

        # Positionen prüfen und schließen
        await self.manage_positions()

    async def manage_positions(self):
        """
        Überwacht und verwaltet offene Positionen.
        """
        positions = self.position_manager.get_active_positions()
        for position in positions:
            token_address = position["token_address"]
            current_price = await self.jupiter.get_token_price(token_address)

            if not current_price:
                self.logger.warning(f"⚠ Preisabfrage fehlgeschlagen für {token_address}")
                continue

            exits = self.position_manager.check_position_exits(current_price)
            for exit_id in exits:
                self.position_manager.close_position(exit_id, current_price)

if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())
