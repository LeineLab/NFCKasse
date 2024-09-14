#!/usr/bin/python3

import busio
import digitalio
from board import SCK, MOSI, MISO, CE0, D25, D24
import RPi.GPIO as GPIO

from adafruit_rgb_display import color565
import adafruit_rgb_display.ili9341 as ili9341

from PIL import Image, ImageDraw, ImageFont

class Display:
	spi = busio.SPI(clock=SCK, MOSI=MOSI, MISO=MISO)
	HEIGHT = 240
	WIDTH  = 320
	image = Image.new("RGB", (WIDTH, HEIGHT))
	draw = ImageDraw.Draw(image)
	font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
	fontsmall = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

	"""Initialize Display with black fill and set brightness to dimmed
	"""
	def __init__(self, CS = CE0, DC = D25, RST = D24, BL = 12):
		self.CS_PIN = CS
		self.DC_PIN = DC
		self.RST_PIN = RST
		self.BL_PIN = BL
		self.display = ili9341.ILI9341(
			self.spi,
			rotation=270,
			baudrate=64000000,
			cs=digitalio.DigitalInOut(self.CS_PIN),
			dc=digitalio.DigitalInOut(self.DC_PIN),
			rst=digitalio.DigitalInOut(self.RST_PIN))
		GPIO.setup(self.BL_PIN, GPIO.OUT)
		GPIO.output(self.BL_PIN, GPIO.LOW)
		self.backlight = GPIO.PWM(self.BL_PIN, 500)
		self.backlight.start(50)
		self.display.fill(0)

	"""Set display brightness 0-255
	"""
	def dim(self, level):
		self.backlight.ChangeDutyCycle(level)

	"""Show two options to choose from

	@param ok	Text of left button
	@param cancel	Text of right button
	"""
	def showOptions(self, ok, cancel):
		text = ok
		print(text)
		(t1, t2, font_width, font_height) = self.fontsmall.getbbox(text)
		self.draw.text((0, self.HEIGHT - font_height), text, font=self.fontsmall, fill=(0,200,0))
		text = cancel
		(t1, t2, font_width, font_height) = self.fontsmall.getbbox(text)
		self.draw.text((self.WIDTH - font_width, self.HEIGHT - font_height), text, font=self.fontsmall, fill=(200,0,0))

	"""Show countdown

	@param button_color	RGB value for countdown
	@param timer	Number to display
	"""
	def showCountdown(self, button_color, timer):
		# clear possible old text
		text = str(timer+1)
		(t1, t2, font_width, font_height) = self.fontsmall.getbbox(text)
		x = (self.WIDTH - font_width) / 2
		y = self.HEIGHT - font_height - 15
		self.draw.rectangle([(x, y), (x+font_width, y+font_height)], fill=(0,0,0))
#		self.draw.text(((self.WIDTH - font_width)/2, self.HEIGHT - font_height - 15), text, font=self.fontsmall, fill=(0,0,0))
		# print new
		text = str(timer)
		(t1, t2, font_width, font_height) = self.fontsmall.getbbox(text)
		self.draw.text(((self.WIDTH - font_width)/2, self.HEIGHT - font_height - 15), text, font=self.fontsmall, fill=(200-button_color * 200,button_color * 200,0))
		self.display.image(self.image)

	"""Show warning, that db is not connected
	"""
	def showNoConnection(self):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Keine Verbindung\nDatenbank offline\nGgf. neu starten", font=self.font, fill=(255,0,0))
		self.display.image(self.image)

	"""Show prompt to present tag
	"""
	def showTag(self):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Karte vorhalten", font=self.font, fill=(255,255,255))
		self.display.image(self.image)

	"""Show prompt to present tag again
	"""
	def showTagAgain(self):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Karte erneut\nvorhalten", font=self.font, fill=(255,255,255))
		self.display.image(self.image)

	"""Show message, that IDs differ
	"""
	def showTagDifferent(self):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Karten-ID weicht ab\nKein Konto angelegt.", font=self.font, fill=(255,0,0))
		self.display.image(self.image)

	"""Show message, that currently the card is unknown
	"""
	def showTagNotKnown(self):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Karte unbekannt", font=self.font, fill=(255,255,255))
		self.showOptions("Neu anlegen","Abbruch")
		self.display.image(self.image)

	"""Show prompt to scan product
	"""
	def showScan(self, value):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Artikel scannen\nDerzeitiges Guthaben:\n%.2f" % value, font=self.font, fill=(255,255,255))
		self.showOptions("","Logout")
		self.display.image(self.image)

	"""Show dialog, if more customer wants to scan more articles
	"""
	def showScanMore(self, value):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Weitere Artikel?\nDerzeitiges Guthaben:\n%.2f" % value, font=self.font, fill=(255,255,255))
		self.showOptions("Artikel scannen","Logout")
		self.display.image(self.image)

	"""Show current value of the card
	"""
	def showValue(self, value):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Hallo!\nDerzeitiges Guthaben:\n%.2f" % value, font=self.font, fill=(255,255,255))
		self.showOptions("Artikel scannen","Logout")
		self.display.image(self.image)

	"""Show message, that barcode scanning was unsuccessful
	"""
	def showNoCode(self):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Kein Barcode erkannt", font=self.font, fill=(255,255,255))
		self.showOptions("Artikel scannen","Logout")
		self.display.image(self.image)

	"""Show message, that the code is not matching any product or topup code
	"""
	def showNoProduct(self):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Produkt nicht gelistet", font=self.font, fill=(255,255,255))
		self.showOptions("Artikel scannen","Logout")
		self.display.image(self.image)

	"""Show message, that the topup code is already redeemed
	"""
	def showTopUpUsed(self):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Aufladecode bereits\nbenutzt. Aufladen\nnicht möglich", font=self.font, fill=(255,255,255))
		self.showOptions("Artikel scannen","Logout")
		self.display.image(self.image)

	"""Show value of topup code
	"""
	def showTopUp(self, value):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Gegenwert:\n%.2f" % (value, ), font=self.font, fill=(255,255,255))
		self.showOptions("Aufladen","Abbruch")
		self.display.image(self.image)

	"""Show product name, price and card value
	"""
	def showProduct(self, name, price, value):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), "Artikel:\n%s\nPreis: %.2f\nGuthaben: %.2f" % (name, price, value), font=self.font, fill=(255,255,255))
		if value < price:
			self.showOptions("Artikel scannen","Abbruch")
		else:
			self.showOptions("Buchen","Abbruch")
		self.display.image(self.image)

"""Unittest sample
"""
if __name__ == '__main__':
	from time import sleep
	disp = Display()
	disp.showScan(123)
	sleep(2)
	disp.showValue(5.32)
	sleep(2)
	disp.showNoCode()
	sleep(2)
	disp.showNoProduct()
	sleep(2)
	disp.showProduct("Premium Cola", 1.0, 542.32)
