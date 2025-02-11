import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import BotLogger


class DexScreener:
    """
    DexScreener API Integration für Token Discovery und Analyse.
    """

    BASE_URL = "https://api.dexscreener.com/latest"

    def __init__(self, logger: BotLogger, filters: Optional[Dict[str, Any]] = None):
        """
        Initialisiert den DexScreener-Service.

        Args:
            logger: Logger-Instanz für Debugging und Fehlermeldungen.
            filters: Filterkriterien für die Token-Suche.
        """
        self.logger = logger
        self.filters = filters or {}

    async def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Führt einen asynchronen API-Request durch.

        Args:
            endpoint: Der spezifische API-Endpunkt.

        Returns:
            API-Antwort als Dictionary.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    self.logger.error(f"API Fehler: {response.status}")
                    return {}
            except Exception as e:
                self.logger.error(f"Fehler bei der API-Anfrage: {str(e)}")
                return {}

    async def fetch_pairs(self, network: str = "solana") -> List[Dict[str, Any]]:
        """
        Ruft alle verfügbaren Token-Paare für das angegebene Netzwerk ab.

        Args:
            network: Blockchain-Netzwerk (z. B. "solana").

        Returns:
            Liste der Token-Paare.
        """
        try:
            response = await self._make_request(f"dex/pairs/{network}")
            return response.get("pairs", [])
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Pairs: {str(e)}")
            return []

    def filter_pairs(self, pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtert die abgerufenen Token-Paare basierend auf den Kriterien.

        Args:
            pairs: Liste von Token-Paaren.

        Returns:
            Gefilterte Token-Paare.
        """
        filtered = []
        for pair in pairs:
            if self._matches_criteria(pair):
                formatted_pair = self._format_pair(pair)
                filtered.append(formatted_pair)
                self.logger.info(f"Gefunden: {formatted_pair['symbol']}")
        return filtered

    def _matches_criteria(self, pair: Dict[str, Any]) -> bool:
        """
        Prüft, ob ein Token-Paar die festgelegten Filterkriterien erfüllt.

        Args:
            pair: Informationen zum Token-Paar.

        Returns:
            True, wenn die Kriterien erfüllt sind.
        """
        try:
            liquidity = float(pair.get("liquidity", {}).get("usd", 0))
            market_cap = float(pair.get("fdv", 0))
            hourly_txns = pair.get("txns", {}).get("h1", {}).get("trades", 0)
            buys = pair.get("txns", {}).get("h1", {}).get("buys", 0)
            sells = pair.get("txns", {}).get("h1", {}).get("sells", 1)  # Vermeide Division durch 0
            buy_sell_ratio = buys / sells

            return (
                liquidity >= self.filters.get("liquidity_min", 0)
                and self.filters["market_cap"]["min"]
                <= market_cap
                <= self.filters["market_cap"]["max"]
                and hourly_txns >= self.filters.get("hourly_transactions", 0)
                and buy_sell_ratio >= self.filters.get("buy_sell_ratio", 0)
            )
        except Exception as e:
            self.logger.warning(f"Kriterienprüfung fehlgeschlagen: {str(e)}")
            return False

    def _format_pair(self, pair: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatiert ein Token-Paar in ein standardisiertes Format.

        Args:
            pair: Informationen zum Token-Paar.

        Returns:
            Ein Wörterbuch mit den wichtigsten Details.
        """
        return {
            "symbol": pair.get("baseToken", {}).get("symbol", "Unknown"),
            "address": pair.get("baseToken", {}).get("address", "Unknown"),
            "price_usd": float(pair.get("priceUsd", 0)),
            "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0)),
            "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
            "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0)),
            "market_cap": float(pair.get("fdv", 0)),
            "dex": pair.get("dexId", "Unknown"),
            "url": pair.get("url", ""),
            "timestamp": datetime.now().isoformat(),
        }

    async def get_filtered_tokens(self, network: str = "solana") -> List[Dict[str, Any]]:
        """
        Abrufen und Filtern von Token-Daten.
        """
        pairs = await self.fetch_pairs(network)
        return self.filter_pairs(pairs)
