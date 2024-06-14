
from pn532pi import Pn532I2c, Pn532, pn532
from hashlib import md5
#import binascii

class NFCtag:
	def __init__(self, port = 1):
		self.i2c = Pn532I2c(port)
		self.nfc = Pn532(self.i2c)
		self.nfc.begin()
		self.nfc.setPassiveActivationRetries(0xFF)
		self.nfc.SAMConfig()

	"""Check if there is a tag available and return hash if present
	"""
	def get(self):
		success, uid = self.nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
		if (success):
			return md5(uid).hexdigest()
		else:
			return None
