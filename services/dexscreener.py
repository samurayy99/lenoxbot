import aiohttp
from typing import Dict, Any, List
from utils.logger import BotLogger

class DexScreener:
    """
    Integration mit der DexScreener API für Token-Daten und Preise.
    """

    def __init__(self, logger: BotLogger, filters: Dict[str, Any]):
        self.BASE_URL = "https://api.dexscreener.com"
        self.logger = logger
        self.filters = filters

    async def get_filtered_tokens(self, chain_id: str = "solana") -> List[Dict[str, Any]]:
        """
        Holt und filtert Token basierend auf den definierten Kriterien.
        
        Args:
            chain_id: Blockchain ID (default: solana)
            
        Returns:
            Liste gefilterter Token-Opportunities
        """
        pairs = await self.fetch_pairs(chain_id)
        if not pairs:
            return []
            
        opportunities = self._filter_opportunities(pairs)
        self.logger.info(f"✅ {len(opportunities)} gefilterte Opportunities gefunden")
        return opportunities

    async def fetch_pairs(self, chain_id: str) -> List[Dict[str, Any]]:
        """
        Ruft Token-Pairs von DexScreener ab.
        """
        try:
            url = f"{self.BASE_URL}/latest/dex/search"
            params = {
                "q": chain_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("pairs", [])
                    else:
                        self.logger.error(f"DexScreener API Error: {response.status}")
                        return []

        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Pairs: {str(e)}")
            return []

    async def get_token_price(self, token_address: str, chain_id: str = "solana") -> float:
        """
        Holt den aktuellen Preis eines Tokens.
        """
        try:
            url = f"{self.BASE_URL}/tokens/v1/{chain_id}/{token_address}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            price_str = data[0].get("priceUsd")
                            if price_str:
                                return float(price_str)
                    return 0.0

        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Token-Preises: {str(e)}")
            return 0.0

    def _filter_opportunities(self, pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtert Token-Pairs basierend auf definierten Kriterien.
        """
        filtered = []
        for pair in pairs:
            try:
                # Extrahiere relevante Daten
                liquidity = pair.get("liquidity", {}).get("usd", 0)
                market_cap = pair.get("marketCap", 0)
                
                # Prüfe Filter-Kriterien
                if (liquidity >= self.filters["liquidity_min"] and
                    self.filters["market_cap"]["min"] <= market_cap <= self.filters["market_cap"]["max"]):
                    
                    filtered.append({
                        "address": pair["baseToken"]["address"],
                        "symbol": pair["baseToken"]["symbol"],
                        "price_usd": float(pair.get("priceUsd", 0)),
                        "liquidity_usd": liquidity,
                        "market_cap": market_cap
                    })
            except Exception as e:
                self.logger.error(f"Fehler beim Filtern eines Pairs: {str(e)}")
                continue

        return filtered