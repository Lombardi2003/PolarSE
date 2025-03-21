import json

FILE_PATH = 'postgres.json'  # File path
DB_NAME, DB_USER, DB_PASSWORD, IP_ADDRESS, PORT_NUMBER, RECONNECT_INTERVAL, RECONNECT_ATTEMPTS = None, None, None, None, None, None, None # Global variables

def load_json_file(FILE_PATH):
    with open(FILE_PATH, 'r') as file:
        data = json.load(file)
    return data

def settings_datebase():
    global DB_NAME, DB_USER, DB_PASSWORD, IP_ADDRESS, PORT_NUMBER, RECONNECT_INTERVAL, RECONNECT_ATTEMPTS
    data = load_json_file(FILE_PATH)

    """Database settings"""
    DB_NAME = data['DATABASE_SETTINGS']['DB_NAME']
    DB_USER = data['DATABASE_SETTINGS']['DB_USER']
    DB_PASSWORD = data['DATABASE_SETTINGS']['DB_PASSWORD']

    """Network settings"""
    IP_ADDRESS = data['NETWORK_SETTINGS']['IP_ADDRESS']
    PORT_NUMBER = data['NETWORK_SETTINGS']['PORT_NUMBER']
    RECONNECT_INTERVAL = data['NETWORK_SETTINGS']['RECONNECT_INTERVAL']
    RECONNECT_ATTEMPTS = data['NETWORK_SETTINGS']['RECONNECT_ATTEMPTS']

def main():
    settings_datebase()
    print(DB_NAME, DB_USER, DB_PASSWORD, IP_ADDRESS, PORT_NUMBER, RECONNECT_INTERVAL, RECONNECT_ATTEMPTS)

if __name__ == '__main__':
    main()