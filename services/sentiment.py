import aiohttp
import os
from typing import Dict, List, Any
from utils.logger import BotLogger

class SentimentAnalyzer:
    """
    Token Sentiment-Analyse mit LunarCrush API.
    """

    def __init__(self, logger: BotLogger):
        """
        Initialisiert den SentimentAnalyzer.

        Args:
            logger: Logger-Instanz für Logging
        """
        self.logger = logger
        self.api_key = os.getenv("LUNARCRUSH_API_KEY")
        self.base_url = "https://lunarcrush.com/api3/"

        if not self.api_key:
            self.logger.error("LUNARCRUSH_API_KEY fehlt! Setze ihn in deiner .env Datei.")

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt eine Anfrage an die LunarCrush API aus.

        Args:
            endpoint: API-Endpunkt (z.B. "assets")
            params: Query-Parameter als Dictionary

        Returns:
            JSON-Antwort als Dictionary oder leeres Dictionary bei Fehler
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    self.logger.error(f"LunarCrush API Fehler: {response.status}")
                    return {}
            except Exception as e:
                self.logger.error(f"LunarCrush Request Fehler: {str(e)}")
                return {}

    async def get_token_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Ruft die Sentiment-Daten eines Tokens ab.

        Args:
            symbol: Token Symbol (z.B. "SOL")

        Returns:
            Sentiment-Daten oder leeres Dictionary bei Fehler
        """
        params = {
            "data": "assets",
            "symbol": symbol
        }
        data = await self._make_request("assets", params)

        if not data or "data" not in data:
            return {}

        token_data = data["data"][0] if data["data"] else {}

        sentiment = {
            "symbol": symbol,
            "galaxy_score": token_data.get("galaxy_score", 0),
            "alt_rank": token_data.get("alt_rank", 0),
            "social_volume": token_data.get("social_volume", 0),
            "social_score": token_data.get("social_score", 0),
            "market_cap_rank": token_data.get("market_cap_rank"),
            "sentiment_absolute": token_data.get("sentiment_absolute", 0),
            "sentiment_relative": token_data.get("sentiment_relative", 0),
            "tweet_volume": token_data.get("tweet_volume", 0),
            "tweet_sentiment": token_data.get("average_sentiment", 0)
        }

        self.logger.info(f"Sentiment-Daten für {symbol}: {sentiment}")
        return sentiment

    async def get_trending_tokens(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Ruft die aktuell trendenden Tokens ab.

        Args:
            limit: Anzahl der zurückzugebenden Tokens

        Returns:
            Liste mit trendenden Token-Daten
        """
        params = {
            "data": "assets",
            "sort": "galaxy_score",  # Beste Sortierung laut Freund
            "limit": limit
        }
        data = await self._make_request("assets", params)

        if not data or "data" not in data:
            return []

        trending_tokens = [
            {
                "symbol": token.get("symbol", ""),
                "galaxy_score": token.get("galaxy_score", 0),
                "alt_rank": token.get("alt_rank", 0),
                "social_score": token.get("social_score", 0)
            }
            for token in data["data"]
        ]

        self.logger.info(f"{len(trending_tokens)} trendende Tokens gefunden.")
        return trending_tokens

    def is_bullish_sentiment(self, sentiment: Dict[str, Any]) -> bool:
        """
        Prüft, ob das Sentiment für einen Token bullish ist.

        Args:
            sentiment: Sentiment-Daten des Tokens

        Returns:
            True wenn bullish, sonst False
        """
        try:
            return (sentiment.get("galaxy_score", 0) >= 60 and sentiment.get("sentiment_relative", 0) > 0.6)
        except Exception as e:
            self.logger.error(f"Fehler bei Bullish-Sentiment-Check: {str(e)}")
            return False
