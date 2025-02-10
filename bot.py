import asyncio
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

        # Laden der Module
        self.dexscreener = DexScreener(self.logger, self.config.get("dexscreener.filters"))
        self.sniffer = SolanaSniffer(self.logger)
        self.jupiter = Jupiter(self.logger)
        self.wallet = PhantomWallet(self.logger)
        self.position_manager = PositionManager(self.logger)
        self.risk_manager = RiskManager(self.logger, self.config.get("trading"))
        self.sentiment_analyzer = SentimentAnalyzer(
            self.config.get("sentiment.api_key"), self.logger
        )

    async def run(self):
        """
        Startet den Trading-Bot.
        """
        self.logger.info("Trading-Bot gestartet.")
        await self.wallet.connect()

        try:
            while True:
                await self.execute_trading_cycle()
                await asyncio.sleep(self.config.get("trading.cycle_interval", 60))
        except KeyboardInterrupt:
            self.logger.info("Bot gestoppt.")
        finally:
            await self.wallet.disconnect()

    async def execute_trading_cycle(self):
        """
        Führt einen kompletten Trading-Zyklus aus.
        """
        self.logger.info("Starte neuen Trading-Zyklus...")
        opportunities = await self.dexscreener.get_trading_opportunities("solana")

        for opportunity in opportunities:
            token_address = opportunity["address"]
            current_price = opportunity["price_usd"]

            # Sicherheitschecks
            if not await self.sniffer.analyze_token(token_address):
                self.logger.warning(f"Token nicht sicher: {token_address}")
                continue

            # Sentiment-Check
            mentions = await self.sentiment_analyzer.get_token_mentions(opportunity["symbol"])
            if not self.sentiment_analyzer.is_bullish_sentiment(mentions):
                self.logger.info(f"Sentiment nicht bullish: {opportunity['symbol']}")
                continue

            # Risiko-Prüfung
            if not self.risk_manager.check_trade_allowed(token_address, opportunity["liquidity_usd"], current_price):
                self.logger.warning(f"Trade nicht erlaubt für {opportunity['symbol']}")
                continue

            # Position eröffnen
            position_size = self.risk_manager.calculate_position_size(current_price, self.risk_manager.get_stop_loss(current_price))
            if not position_size:
                self.logger.warning(f"Positionsgröße zu klein für {opportunity['symbol']}")
                continue

            # Trading ausführen
            swap_tx = await self.jupiter.execute_trade(token_address, position_size)
            if not swap_tx:
                self.logger.error(f"Trade fehlgeschlagen für {opportunity['symbol']}")
                continue

            # Position speichern
            stop_loss = self.risk_manager.get_stop_loss(current_price)
            take_profit = self.risk_manager.get_take_profit(current_price)
            self.position_manager.open_position(token_address, current_price, position_size, stop_loss, take_profit)
            self.logger.info(f"Trade ausgeführt: {opportunity['symbol']} | Größe: {position_size}")

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
                self.logger.warning(f"Preisabfrage fehlgeschlagen für {token_address}")
                continue

            exits = self.position_manager.check_position_exits(current_price)
            for exit_id in exits:
                self.position_manager.close_position(exit_id, current_price)

if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())
