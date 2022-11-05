
import serial
import RPi.GPIO as GPIO

class BarcodeScanner:
	def __init__(self, trigger_pin, port = '/dev/ttyAMA0', baudrate = 9600, timeout = 1):
		self.trigger_pin = trigger_pin
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.trigger_pin, GPIO.OUT)
		GPIO.output(self.trigger_pin, 1)
		self.__buffer = b''
		self.conn = serial.Serial(port, baudrate, timeout = timeout)

	def scan(self):
		GPIO.output(self.trigger_pin, 0)
		while self.conn.in_waiting:
			c = self.conn.read()
			if c == b'\r' or c == b'\n':
				if len(self.__buffer):
					tmp = self.__buffer
					self.__buffer = b''
					return tmp
			else:
				self.__buffer += c
		return None

	def endScan(self):
		GPIO.output(self.trigger_pin, 1)
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
