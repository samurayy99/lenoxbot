from gmgn_wrapper.gmgn.client import gmgn
import logging
import time
from datetime import datetime
from tabulate import tabulate

class SmartMoneyFollower:
    def __init__(self):
        self.gmgn = gmgn()  # Initialize GMGN client
        self.logger = logging.getLogger("SmartMoneyFollower")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def get_top_wallets(self, timeframe="7d", walletTag="smart_degen"):
        """Fetch top wallets from GMGN."""
        try:
            response = self.gmgn.getTrendingWallets(timeframe, walletTag)
            if not response or not isinstance(response, dict) or 'rank' not in response:
                self.logger.error("❌ No or invalid response from getTrendingWallets.")
                return []
            return response['rank']
        except Exception as e:
            self.logger.error(f"❌ Error fetching wallets: {e}")
            return []

    def analyze_wallet_activity(self, wallet_address, period="7d"):
        """Analysiert Wallet-Aktivität"""
        try:
            response = self.gmgn.getWalletInfo(walletAddress=wallet_address, period=period)
            if not response or not isinstance(response, dict):
                self.logger.error(f"❌ Ungültige Antwort für Wallet {wallet_address}")
                return {}
            
            # Detaillierte Analyse ausgeben
            if response.get('realizedPnl') and response.get('winRate'):
                self.logger.info(f"""
                💰 Wallet Performance: {wallet_address}
                Profit: {response.get('realizedPnl')} SOL
                Win-Rate: {float(response.get('winRate', 0)) * 100:.1f}%
                Trades: {response.get('buyCount', 0)} buys, {response.get('sellCount', 0)} sells
                Last Active: {datetime.fromtimestamp(response.get('lastActiveTimestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}
                """)
            
            return response
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Wallet-Analyse {wallet_address}: {e}")
            return {}

    def evaluate_token(self, token_address):
        """Fetch token information and price."""
        try:
            token_info = self.gmgn.getTokenInfo(contractAddress=token_address)
            token_price = self.gmgn.getTokenUsdPrice(contractAddress=token_address)
            if not token_info:
                self.logger.warning(f"⚠️ No token info for {token_address}")
            return token_info, token_price
        except Exception as e:
            self.logger.error(f"❌ Error evaluating token: {e}")
            return {}, {}

    def print_analysis_output(self, wallets):
        """Print analysis results in a table."""
        if not wallets:
            self.logger.warning("⚠️ No wallets meet the criteria.")
            return
        headers = ["Rank", "Wallet Address", "Realized Profit (SOL)", 
                  "Buy Transactions", "Sell Transactions", "Last Active"]
        table_data = []
        for idx, wallet in enumerate(wallets):
            last_active = datetime.utcfromtimestamp(
                wallet.get('last_active_timestamp', 0) or 0
            ).strftime('%Y-%m-%d %H:%M:%S')
            table_data.append([
                idx + 1,
                wallet.get('wallet_address', 'N/A'),
                wallet.get('realized_profit', 'N/A'),
                wallet.get('buy', 'N/A'),
                wallet.get('sell', 'N/A'),
                last_active
            ])
        print(tabulate(table_data, headers=headers, tablefmt="pretty"))
        print("\n💰 Note: 'Realized Profit' is in SOL.")

    def run_strategy(self):
        """Main strategy to analyze top wallets."""
        try:
            self.logger.info("🚀 Starting Smart Money Analysis...")
            top_wallets = self.get_top_wallets()
            if not top_wallets:
                self.logger.warning("❌ No top wallets found.")
                return
            self.logger.info(f"✅ Found {len(top_wallets)} top wallets.")
            wallet_data = []
            for wallet in top_wallets:
                wallet_address = wallet.get('wallet_address')
                self.logger.info(f"📊 Analyzing wallet: {wallet_address}")
                wallet_activity = self.analyze_wallet_activity(wallet_address)
                if not wallet_activity:
                    continue
                winrate = wallet_activity.get('winrate', 0) or 0
                if winrate > 0.50:
                    wallet_data.append(wallet_activity)
                    time.sleep(1)
            self.print_analysis_output(wallet_data)
        except Exception as e:
            self.logger.error(f"❌ Error in strategy: {e}")

if __name__ == "__main__":
    follower = SmartMoneyFollower()
    follower.run_strategy()
