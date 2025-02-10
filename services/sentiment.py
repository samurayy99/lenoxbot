import aiohttp
from typing import Dict, List, Any
from utils.logger import BotLogger


class SentimentAnalyzer:
    """
    Token Sentiment-Analyse mit TweetScout Integration.
    """

    def __init__(self, api_key: str, logger: BotLogger):
        """
        Initialisiert den SentimentAnalyzer.

        Args:
            api_key: TweetScout API-Key
            logger: Logger-Instanz
        """
        self.BASE_URL = "https://api.tweetscout.io/v1"
        self.api_key = api_key
        self.logger = logger

    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Führt einen TweetScout API-Request aus.

        Args:
            endpoint: API-Endpunkt
            params: Query-Parameter

        Returns:
            API-Antwort als Dictionary
        """
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    self.logger.error(f"TweetScout API Fehler: {response.status}")
                    return {}
            except Exception as e:
                self.logger.error(f"TweetScout Request Fehler: {str(e)}")
                return {}

    async def get_token_mentions(self, token: str) -> Dict[str, Any]:
        """
        Analysiert Twitter-Erwähnungen eines Tokens.

        Args:
            token: Token Symbol (z.B. "SOL")

        Returns:
            Mentions-Statistiken
        """
        try:
            params = {"token": token}
            data = await self._make_request("mentions", params)
            
            if not data:
                return {}
                
            mentions = {
                "count_24h": data.get("mentions_24h", 0),
                "sentiment_score": data.get("sentiment", 0),
                "engagement": data.get("engagement", 0),
                "influencer_mentions": data.get("influencer_count", 0)
            }
            
            self.logger.info(f"Token {token} Mentions analysiert: {mentions['count_24h']}")
            return mentions
            
        except Exception as e:
            self.logger.error(f"Mentions-Analyse Fehler: {str(e)}")
            return {}

    async def get_trending_tokens(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Ruft aktuell trendende Tokens ab.

        Args:
            limit: Maximale Anzahl der Tokens

        Returns:
            Liste der trendenden Tokens
        """
        try:
            params = {"limit": limit}
            data = await self._make_request("trending", params)
            
            if not data or "tokens" not in data:
                return []
                
            trending = data["tokens"]
            self.logger.info(f"{len(trending)} trendende Tokens gefunden")
            return trending
            
        except Exception as e:
            self.logger.error(f"Trending Tokens Fehler: {str(e)}")
            return []

    async def get_sentiment_alerts(self) -> List[Dict[str, Any]]:
        """
        Ruft aktuelle Sentiment-Alerts ab.

        Returns:
            Liste von Sentiment-Alerts
        """
        try:
            data = await self._make_request("alerts")
            
            if not data or "alerts" not in data:
                return []
                
            alerts = data["alerts"]
            self.logger.info(f"{len(alerts)} Sentiment-Alerts gefunden")
            return alerts
            
        except Exception as e:
            self.logger.error(f"Sentiment-Alerts Fehler: {str(e)}")
            return []

    def is_bullish_sentiment(self, mentions: Dict[str, Any]) -> bool:
        """
        Prüft ob das Sentiment bullish ist.

        Args:
            mentions: Token-Mentions Daten

        Returns:
            True wenn bullish
        """
        try:
            # Mindestens 100 Mentions und positiver Sentiment-Score
            return (mentions.get("count_24h", 0) >= 100 and 
                    mentions.get("sentiment_score", 0) > 0.6)
        except Exception as e:
            self.logger.error(f"Sentiment-Check Fehler: {str(e)}")
            return False