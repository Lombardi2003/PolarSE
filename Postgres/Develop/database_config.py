import json

FILE_PATH = 'postgres.json'  # File path

class DatabaseConfig:
    def __init__(self):
        self.load_settings()

    def load_settings(self):
        with open(FILE_PATH, 'r') as file:
            data = json.load(file)

        # Database settings
        self.DB_NAME = data['DATABASE_SETTINGS']['DB_NAME']
        self.DB_USER = data['DATABASE_SETTINGS']['DB_USER']
        self.DB_PASSWORD = data['DATABASE_SETTINGS']['DB_PASSWORD']

        # Network settings
        self.IP_ADDRESS = data['NETWORK_SETTINGS']['IP_ADDRESS']
        self.PORT_NUMBER = data['NETWORK_SETTINGS']['PORT_NUMBER']
        self.RECONNECT_INTERVAL = data['NETWORK_SETTINGS']['RECONNECT_INTERVAL']
        self.RECONNECT_ATTEMPTS = data['NETWORK_SETTINGS']['RECONNECT_ATTEMPTS']
    def get_name(self):
        return self.DB_NAME