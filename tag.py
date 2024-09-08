from pn532pi import Pn532I2c, Pn532, pn532
from hashlib import md5

class NFCtag:
	def __init__(self, port = 1, uid_hash = True):
		self.i2c = Pn532I2c(port)
		self.nfc = Pn532(self.i2c)
		self.nfc.begin()
		self.nfc.setPassiveActivationRetries(0xFF)
		self.nfc.SAMConfig()
		self.uid_hash = uid_hash

	"""Check if there is a tag available and return hash if present
	"""
	def get(self):
		success, uid = self.nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
		if (success):
			if self.uid_hash:
				return md5(uid).hexdigest()
			else:
				tag_uid = 0
				for i in uid:
					tag_uid <<= 8
					tag_uid += i
				return tag_uid
		else:
			return None

if __name__ == '__main__':
	oldTag = None
	nfctag = NFCtag(uid_hash = False)
	while True:
		tag = nfctag.get()
		if tag != oldTag:
			oldTag = tag
			if tag is not None:
				print("Found new Tag, Hash is %s" % tag)
