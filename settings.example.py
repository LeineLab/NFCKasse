# NFCKasse settings - copy to settings.py and fill in your values

# MakerSpaceAPI connection
api_url   = 'http://localhost:8000'
api_token = ''  # Bearer token for this checkout-box device (from MakerSpaceAPI admin)

# Serial port for barcode scanner, when using the Pis bus: /dev/ttyACM0
serialport = '/dev/ttyUSB0'

# Optional guest card UID (raw integer, or None to disable)
uid_guest = None

# Optional: MQTT/HomeAssistant
#mqtt_host = 'mqtt.hacker.space'
#mqtt_user = 'nfc_kasse'
#mqtt_password = 'password'
