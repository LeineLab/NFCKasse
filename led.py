
import RPi.GPIO as GPIO

class LED:
	def __init__(self, r, g, b):
		self.r = r
		self.g = g
		self.b = b
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(r, GPIO.OUT)
		GPIO.setup(g, GPIO.OUT)
		GPIO.setup(b, GPIO.OUT)

	def clear(self):
		GPIO.output(self.r, 1)
		GPIO.output(self.g, 1)
		GPIO.output(self.b, 1)

	def red(self):
		self.clear()
		GPIO.output(self.r, 0)

	def green(self):
		self.clear()
		GPIO.output(self.g, 0)

	def blue(self):
		self.clear()
		GPIO.output(self.b, 0)

	def yellow(self):
		self.clear()
		GPIO.output(self.r, 0)
		GPIO.output(self.g, 0)

	def purple(self):
		self.clear()
		GPIO.output(self.r, 0)
		GPIO.output(self.b, 0)

	def cyan(self):
		self.clear()
		GPIO.output(self.g, 0)
		GPIO.output(self.b, 0)

	def white(self):
		GPIO.output(self.r, 0)
		GPIO.output(self.g, 0)
		GPIO.output(self.b, 0)

"""Unittest
"""
if __name__ == '__main__':
	import time
	led = LED(5, 13, 6)
	led.red()
	time.sleep(1)
	led.green()
	time.sleep(1)
	led.blue()
	time.sleep(1)
	led.clear()
