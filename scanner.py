
import serial
import RPi.GPIO as GPIO

class BarcodeScanner:
	def __init__(self, trigger_pin = -1, port = '/dev/ttyAMA0', baudrate = 9600, timeout = 1):
		self.trigger_pin = trigger_pin
		if trigger_pin != -1:
			#Setup GPIO for scan trigger if configured
			GPIO.setmode(GPIO.BCM)
			GPIO.setup(self.trigger_pin, GPIO.OUT)
			GPIO.output(self.trigger_pin, 1)
		self.__buffer = b''
		self.conn = serial.Serial(port, baudrate, timeout = timeout)

	"""Try to scan barcode, return None if none is found
	"""
	def scan(self, repeated_scan):
		if self.trigger_pin != -1:
			#Enable trigger pin
			GPIO.output(self.trigger_pin, 0)
		elif not repeated_scan:
			#Scan will be active for set time, no need to resend on every interval
			#Enable serial control
			self.conn.write(b'\x7E\x00\x08\x01\x00\x00\xD5\xAB\xCD')
			#Extend time to 20s zone 0x0006 = C8h / 200d
			self.conn.write(b'\x7E\x00\x08\x01\x00\x06\xC8\xAB\xCD')
			#Trigger scanning
			self.conn.write(b'\x7E\x00\x08\x01\x00\x02\x01\xAB\xCD')
		while self.conn.in_waiting:
			c = self.conn.read()
			if c == b'\r' or c == b'\n':
				if len(self.__buffer):
					tmp = self.__buffer
					self.__buffer = b''
					return tmp
			else:
				self.__buffer += c
				if self.__buffer == b'\x02\x00\x00\x01\x00\x33\x31':
					self.__buffer = b'' # remove handshake notice
		return None

	"""Release trigger
	"""
	def endScan(self):
		if self.trigger_pin != -1:
			#Disable trigger pin
			GPIO.output(self.trigger_pin, 1)
		else:
			#Switch to manual trigger
			self.conn.write(b'\x7E\x00\x08\x01\x00\x00\xD4\xAB\xCD')
		self.__buffer = b''

if __name__ == '__main__':
	scanner = BarcodeScanner(18, '/dev/ttyS0')
	import time
	timeout = time.time() + 5
	res = None
	while res is None and timeout > time.time():
		res = scanner.scan()
	scanner.endScan()
	print(res)
