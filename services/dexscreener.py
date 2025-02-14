import aiohttp
from typing import List, Dict, Any
from utils.logger import BotLogger

class DexScreener:
    """
    Integration with the Dexscreener API for fetching trading opportunities.
    Documentation: https://docs.dexscreener.com/api/
    """

    def __init__(self, logger: BotLogger, filters: Dict[str, Any]):
        self.BASE_URL = "https://api.dexscreener.com/latest/dex"
        self.logger = logger
        self.filters = filters

    async def get_filtered_tokens(self, chain: str) -> List[Dict[str, Any]]:
        """
        Fetches filtered tokens for a specific blockchain.

        Args:
            chain: The blockchain to fetch tokens from (e.g., "solana").

        Returns:
            A list of filtered tokens.
        """
        try:
            url = f"{self.BASE_URL}/{chain}/pairs"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"Fetched {len(data['pairs'])} pairs for {chain}.")
                        return data['pairs']
                    else:
                        error_data = await response.text()
                        self.logger.error(f"DexScreener API Error: {response.status} - {error_data}")
                        return []

        except Exception as e:
            self.logger.error(f"Error fetching filtered tokens: {str(e)}")
            return []

    async def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        Fetches information about a specific token.

        Args:
            token_address: The address of the token.

        Returns:
            A dictionary containing token information.
        """
        try:
            url = f"{self.BASE_URL}/tokens/{token_address}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"Fetched info for token: {token_address}.")
                        return data
                    else:
                        error_data = await response.text()
                        self.logger.error(f"DexScreener API Error: {response.status} - {error_data}")
                        return {}

        except Exception as e:
            self.logger.error(f"Error fetching token info: {str(e)}")
            return {}