import random
import tls_client
from fake_useragent import UserAgent
from typing import Dict, Any

class gmgn:
    BASE_URL = "https://gmgn.ai/defi/quotation"

    def __init__(self):
        self.randomiseRequest()

    def randomiseRequest(self) -> None:
        """Initialize request settings with randomized parameters."""
        self.identifier = random.choice([
            browser for browser in tls_client.settings.ClientIdentifiers.__args__ 
            if browser.startswith(('chrome', 'safari', 'firefox', 'opera'))
        ])
        self.sendRequest = tls_client.Session(
            random_tls_extension_order=True, 
            client_identifier=self.identifier
        )

        parts = self.identifier.split('_')
        identifier, version, *_ = parts

        os = 'windows'
        if identifier == 'opera':
            identifier = 'chrome'
        elif version == 'ios':
            os = 'ios'

        self.user_agent = UserAgent(browsers=[identifier], os=[os]).random
        self.headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://gmgn.ai/?chain=sol',
            'user-agent': self.user_agent
        }

    def getTokenInfo(self, contractAddress: str) -> Dict[str, Any]:
        """
        Gets info on a token.
        
        Args:
            contractAddress: The contract address to query
            
        Returns:
            Dict containing token information or empty dict if invalid
        """
        self.randomiseRequest()
        if not contractAddress:
            return {}
            
        url = f"{self.BASE_URL}/v1/tokens/sol/{contractAddress}"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json()
    
    def getNewPairs(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get new trading pairs with optional limit.
        
        Args:
            limit: Maximum number of pairs to return (default 50)
            
        Returns:
            Dict containing pairs data or empty dict if invalid
        """
        self.randomiseRequest()
        if not isinstance(limit, int) or limit > 50:
            return {}
        
        url = f"{self.BASE_URL}/v1/pairs/sol/new_pairs?limit={limit}&orderby=open_timestamp&direction=desc&filters[]=not_honeypot"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})
    
    def getTrendingWallets(self, timeframe: str = "7d", walletTag: str = "smart_degen") -> Dict[str, Any]:
        """
        Gets a list of trending wallets based on timeframe and wallet tag.

        Args:
            timeframe: Time period ("1d", "7d", "30d")
            walletTag: Type of wallet ("pump_smart", "smart_degen", "reowned", "snipe_bot")
            
        Returns:
            Dict containing wallet data or empty dict if invalid
        """
        self.randomiseRequest()
        valid_timeframes = ["1d", "7d", "30d"]
        valid_tags = ["pump_smart", "smart_degen", "reowned", "snipe_bot"]
        
        if timeframe not in valid_timeframes or walletTag not in valid_tags:
            return {}
        
        url = f"{self.BASE_URL}/v1/rank/sol/wallets/{timeframe}?tag={walletTag}&orderby=pnl_{timeframe}&direction=desc"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})
    
    def getTrendingTokens(self, timeframe: str = "1h") -> Dict[str, Any]:
        """
        Gets a list of trending tokens based on timeframe.
        
        Args:
            timeframe: Time period ("1m", "5m", "1h", "6h", "24h")
            
        Returns:
            Dict containing token data or empty dict if invalid
        """
        timeframes = ["1m", "5m", "1h", "6h", "24h"]
        self.randomiseRequest()
        
        if timeframe not in timeframes:
            return {}

        url = (f"{self.BASE_URL}/v1/rank/sol/swaps/{timeframe}?orderby=swaps&direction=desc"
               f"{'&limit=20' if timeframe == '1m' else ''}")
        
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})

    def getTokensByCompletion(self, limit: int = 50) -> Dict[str, Any]:
        """
        Gets tokens by their bonding curve completion progress.
        
        Args:
            limit: Maximum number of tokens to return (default 50)
            
        Returns:
            Dict containing token data or empty dict if invalid
        """
        self.randomiseRequest()
        if not isinstance(limit, int) or limit > 50:
            return {}

        url = f"{self.BASE_URL}/v1/rank/sol/pump?limit={limit}&orderby=progress&direction=desc&pump=true"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})
    
    def findSnipedTokens(self, size: int = 10) -> Dict[str, Any]:
        """
        Gets a list of tokens that have been sniped.
        
        Args:
            size: Number of tokens to return (default 10, max 39)
            
        Returns:
            Dict containing sniped token data or empty dict if invalid
        """
        self.randomiseRequest()
        if not isinstance(size, int) or size > 39:
            return {}
        
        url = f"{self.BASE_URL}/v1/signals/sol/snipe_new?size={size}&is_show_alert=false&featured=false"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})

    def getGasFee(self) -> Dict[str, Any]:
        """
        Get the current gas fee price.
        
        Returns:
            Dict containing gas fee data
        """
        self.randomiseRequest()
        url = f"{self.BASE_URL}/v1/chains/sol/gas_price"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})
    
    def getTokenUsdPrice(self, contractAddress: str) -> Dict[str, Any]:
        """
        Get the realtime USD price of the token.
        
        Args:
            contractAddress: The contract address to query
            
        Returns:
            Dict containing price data or empty dict if invalid
        """
        self.randomiseRequest()
        if not contractAddress:
            return {}
        
        url = f"{self.BASE_URL}/v1/sol/tokens/realtime_token_price?address={contractAddress}"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})

    def getTopBuyers(self, contractAddress: str) -> Dict[str, Any]:
        """
        Get the top buyers of a token.
        
        Args:
            contractAddress: The contract address to query
            
        Returns:
            Dict containing buyer data or empty dict if invalid
        """
        self.randomiseRequest()
        if not contractAddress:
            return {}
        
        url = f"{self.BASE_URL}/v1/tokens/top_buyers/sol/{contractAddress}"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})

    def getSecurityInfo(self, contractAddress: str) -> Dict[str, Any]:
        """
        Gets security info about the token.
        
        Args:
            contractAddress: The contract address to query
            
        Returns:
            Dict containing security data or empty dict if invalid
        """
        self.randomiseRequest()
        if not contractAddress:
            return {}
        
        url = f"{self.BASE_URL}/v1/tokens/security/sol/{contractAddress}"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})
    
    def getWalletInfo(self, walletAddress: str, period: str = "7d") -> Dict[str, Any]:
        """
        Gets various information about a wallet address.
        
        Args:
            walletAddress: The wallet address to query
            period: Time period ("7d", "30d")
            
        Returns:
            Dict containing wallet data or empty dict if invalid
        """
        self.randomiseRequest()
        valid_periods = ["7d", "30d"]

        if not walletAddress or period not in valid_periods:
            return {}
        
        url = f"{self.BASE_URL}/v1/smartmoney/sol/walletNew/{walletAddress}?period={period}"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json().get('data', {})