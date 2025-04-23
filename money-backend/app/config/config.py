from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-this')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False  # Preserve JSON response order
    
    # TradeRepublic bank account configuration
    TRADEREPUBLIC_IBAN = os.environ.get("TRADEREPUBLIC_IBAN", "DE12345678901234567890")
    TRADEREPUBLIC_SAVING_PLAN_IBAN = os.environ.get("TRADEREPUBLIC_SAVING_PLAN_IBAN", "DE09876543210987654321")
    
    @property
    def own_ibans(self):
        """
        Returns a list of all IBANs that belong to the user.
        Used for detecting internal transfers.
        """
        return [
            self.TRADEREPUBLIC_IBAN,
            self.TRADEREPUBLIC_SAVING_PLAN_IBAN,
            # Add additional IBANs as needed
        ]

# Create a singleton instance of the config
config = Config()