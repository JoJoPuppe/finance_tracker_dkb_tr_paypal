"""
Application configuration settings

This module provides centralized access to configuration values from various sources:
- Environment variables
- Configuration files
- Default values

Usage:
    from app.config import config

    # Access configuration values
    tr_iban = config.TRADEREPUBLIC_IBAN
    tr_internal_iban = config.TRADEREPUBLIC_INTERNAL_IBAN
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parents[2] / ".env"
load_dotenv(env_path)


class Config:
    """Configuration container class with properties for all app settings"""

    # Bank account IBANs
    TRADEREPUBLIC_IBAN = os.environ.get(
        "TRADEREPUBLIC_IBAN", "DE12345678901234567890"
    )  # Default for development only
    TRADEREPUBLIC_SAVING_PLAN_IBAN = os.environ.get(
        "TRADEREPUBLIC_SAVING_PLAN_IBAN", "DE09876543210987654321"
    )  # Default for development only

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

