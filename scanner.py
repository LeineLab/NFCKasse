
import serial
import RPi.GPIO as GPIO

class BarcodeScanner:
	def __init__(self, trigger_pin, port = '/dev/ttyAMA0', baudrate = 9600, timeout = 1):
		self.trigger_pin = trigger_pin
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.trigger_pin, GPIO.OUT)
		GPIO.output(self.trigger_pin, 1)
		self.conn = serial.Serial(port, baudrate, timeout = timeout)

	def scan(self):
		GPIO.output(self.trigger_pin, 0)
		line = self.conn.read_until()
		GPIO.output(self.trigger_pin, 1)
		line = line.strip()
		if line == b'':
			return None
		return line
