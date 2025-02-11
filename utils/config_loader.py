import os
import json
from dotenv import load_dotenv
from typing import Dict, Any

class ConfigLoader:
    """
    Lädt und verwaltet die Bot-Konfiguration aus .env und config.json
    """

    def __init__(self, env_file: str = ".env", config_file: str = "config.json"):
        """
        Initialisiert den ConfigLoader und lädt Konfigurationen.
        """
        self.env_file = env_file
        self.config_file = config_file
        
        # Lade Umgebungsvariablen
        load_dotenv(env_file)

        # Standard-Konfiguration
        self.default_config = {
            'trading': {
                'network': 'solana',
                'max_active_trades': 3,
                'position_size': 0.1,  # SOL
                'max_budget': 2.0      # SOL
            },
            'dexscreener': {
                'filters': {
                    'liquidity_min': 20_000,
                    'market_cap': {'min': 100_000, 'max': 2_000_000},
                    'hourly_transactions': 200,
                    'buy_sell_ratio': 1.5
                }
            },
            'jupiter': {
                'slippage_max': 0.01,
                'route_preference': 'best'
            },
            'exit': {
                'take_profit': 0.4,
                'stop_loss': 0.15,
                'trailing_stop': {
                    'activation': 0.2,
                    'distance': 0.1
                },
                'max_hold_time': 24
            }
        }

        # Lade JSON und merge mit Defaults
        self.config_data = self._load_json_config()

    def _load_json_config(self) -> Dict[str, Any]:
        """
        Lädt Konfigurationsdaten aus einer JSON-Datei und merged sie mit Defaults.
        """
        config = self.default_config.copy()
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as file:
                    user_config = json.load(file)
                    self._deep_update(config, user_config)
            except json.JSONDecodeError as e:
                raise ValueError(f"Fehler beim Laden von {self.config_file}: {e}")
        return config

    def _deep_update(self, base: Dict, updates: Dict) -> None:
        """
        Aktualisiert rekursiv ein verschachteltes Dictionary.
        """
        for key, value in updates.items():
            if isinstance(value, dict) and key in base:
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Holt einen Wert aus ENV > JSON > Default-Werten.
        """
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value
        
        keys = key.split('.')
        value = self.config_data
        for k in keys:
            if k in value:
                value = value[k]
            else:
                return default
        return value

    def save_state(self, state: Dict[str, Any], filename: str = 'data/trading_state.json') -> None:
        """
        Speichert den aktuellen Trading-Zustand in einer JSON-Datei.
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as file:
            json.dump(state, file, indent=4)

    def load_state(self, filename: str = 'data/trading_state.json') -> Dict[str, Any]:
        """
        Lädt einen gespeicherten Trading-Zustand aus einer JSON-Datei.
        """
        try:
            with open(filename, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def validate(self) -> bool:
        """
        Validiert die Konfiguration auf Vollständigkeit und Konsistenz.
        """
        required_env_vars = ['BOT_WALLET_ADDRESS', 'BOT_PRIVATE_KEY']
        for var in required_env_vars:
            if not os.getenv(var):
                raise ValueError(f"Fehlende Umgebungsvariable: {var}")

        if self.get('trading.position_size') > self.get('trading.max_budget'):
            raise ValueError("Position Size kann nicht größer als Max Budget sein.")
        
        return True
