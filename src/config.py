import os
from typing import Optional
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        # Redmine Configuration
        self.REDMINE_URL = self._get_env('REDMINE_URL')
        self.REDMINE_API_KEY = self._get_env('REDMINE_API_KEY')
        
        # OpenAI Configuration
        self.OPENAI_API_KEY = self._get_env('OPENAI_API_KEY')
        
        # Application Configuration
        self.DEBUG = self._get_env('DEBUG', 'False').lower() == 'true'
        self.LOG_LEVEL = self._get_env('LOG_LEVEL', 'INFO')
        
        # Performance Configuration
        self.CACHE_TTL = int(self._get_env('CACHE_TTL', '300'))
        self.REQUEST_TIMEOUT = int(self._get_env('REQUEST_TIMEOUT', '30'))
        self.RATE_LIMIT_REQUESTS = int(self._get_env('RATE_LIMIT_REQUESTS', '100'))
        self.RATE_LIMIT_PERIOD = int(self._get_env('RATE_LIMIT_PERIOD', '60'))
        
        # Data Export Configuration
        self.MAX_EXPORT_ROWS = int(self._get_env('MAX_EXPORT_ROWS', '10000'))

    def _get_env(self, key: str, default: Optional[str] = None) -> str:
        """Get environment variable with validation."""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Environment variable {key} is not set")
        return value

config = Config()