import aiohttp
from typing import Dict, Any, Optional
from utils.logger import BotLogger

class SolanaSniffer:
    """
    SolanaSniffer überprüft Token auf der Solana-Blockchain auf potenzielle Sicherheitsrisiken.
    """

    BASE_URL = "https://api.solanasniffer.com/v1"

    def __init__(self, logger: Optional[BotLogger] = None):
        """
        Initialisiert den SolanaSniffer-Service.

        Args:
            logger: Logger-Instanz für Debugging und Protokollierung
        """
        self.logger = logger or BotLogger()

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt einen API-Request durch.

        Args:
            endpoint: API-Endpunkt
            params: Query-Parameter für die Anfrage

        Returns:
            Antwortdaten als Dictionary
        """
        url = f"{self.BASE_URL}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(f"SolanaSniffer API-Fehler: {response.status}")
                        return {}
            except Exception as e:
                self.logger.error(f"Fehler bei der Anfrage an SolanaSniffer: {str(e)}")
                return {}

    async def check_contract(self, token_address: str) -> Dict[str, Any]:
        """
        Überprüft einen Token auf Sicherheitsrisiken.

        Args:
            token_address: Adresse des zu überprüfenden Tokens

        Returns:
            Sicherheitsbewertung und Analyseergebnisse
        """
        try:
            response = await self._make_request("analyze", {"address": token_address})
            if response and "safety_score" in response:
                self.logger.info(f"Token-Sicherheitsbewertung: {response['safety_score']} für {token_address}")
                return response
            else:
                self.logger.warning(f"Keine Sicherheitsbewertung für Token: {token_address}")
                return {}
        except Exception as e:
            self.logger.error(f"Fehler bei der Sicherheitsprüfung des Tokens: {str(e)}")
            return {}

    def is_safe(self, analysis: Dict[str, Any], threshold: int = 85) -> bool:
        """
        Überprüft, ob ein Token als sicher gilt.

        Args:
            analysis: Analyseergebnisse des Tokens
            threshold: Mindestbewertung für Sicherheit (default: 85)

        Returns:
            True, wenn das Token sicher ist, sonst False
        """
        safety_score = analysis.get("safety_score", 0)
        is_safe = safety_score >= threshold
        if not is_safe:
            self.logger.warning(f"Token nicht sicher: Sicherheitsbewertung {safety_score} (Schwelle: {threshold})")
        return is_safe