import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from app import create_app

# Set up logger
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Create logger
logger = logging.getLogger('money_backend')
logger.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create file handler for logging to a file (with log rotation)
log_file = os.path.join(log_dir, f'money_backend_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)  # 10MB max size, 10 backup files
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create console handler for logging to stdout
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = create_app()

# Add logger to the Flask app
app.logger.handlers.clear()  # Remove default Flask logger handlers
for handler in logger.handlers:
    app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    logger.info("Starting Money Backend Application")
    app.run(debug=True, port=5005)
