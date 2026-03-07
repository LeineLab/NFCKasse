#!/usr/bin/env python3

import busio
import digitalio
from board import SCK, MOSI, MISO, CE0, D25, D24
import RPi.GPIO as GPIO
import qrcode

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

	def _wrap_text(self, msg : str) -> str:
		"""Word-wrap msg to fit within WIDTH pixels.
		Explicit \n are preserved. Tokens containing non-breaking spaces
		(\u00a0) are treated as indivisible; they are replaced with regular
		spaces in the output after wrapping.
		"""
		result_lines = []
		for paragraph in msg.split('\n'):
			words = paragraph.split(' ')
			line = ''
			for word in words:
				candidate = (line + ' ' + word).lstrip(' ')
				if self.font.getbbox(candidate)[2] <= self.WIDTH:
					line = candidate
				else:
					if line:
						result_lines.append(line.replace('\u00a0', ' '))
					line = word
			result_lines.append(line.replace('\u00a0', ' '))
		return '\n'.join(result_lines)

	def dialog(self, msg : str, btn1 : str, btn2 : str, color : tuple[int, int, int]):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		self.draw.text((0, 0), self._wrap_text(msg), font=self.font, fill=color)
		self.showOptions(btn1, btn2)
		self.display.image(self.image)

	def error(self, msg, btn1 = "", btn2 = ""):
		self.dialog(msg, btn1, btn2, (255, 0, 0))

	def info(self, msg, btn1 = "", btn2 = ""):
		self.dialog(msg, btn1, btn2, (255, 255, 0))

	def success(self, msg, btn1 = "", btn2 = ""):
		self.dialog(msg, btn1, btn2, (0, 255, 0))

	def message(self, msg, btn1 = "", btn2 = ""):
		self.dialog(msg, btn1, btn2, (255, 255, 255))

	"""Show QR-Code
	"""
	def showQR(self, data):
		self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
		qr = qrcode.QRCode(box_size=3, border=0)
		qr.add_data(data)
		img = qr.make_image(back_color=(0, 0, 0), fill_color=(255, 255, 255)).convert("RGB")
		self.image.paste(img, (int((self.WIDTH - (img.size)[0]) / 2), 0))
		self.display.image(self.image)

"""Unittest sample
"""
if __name__ == '__main__':
	from time import sleep
	disp = Display()
	disp.error("Error")
	sleep(2)
	disp.info("Info")
	sleep(2)
	disp.success("Success")
	sleep(2)
	disp.message("Message")
	sleep(2)
	disp.showQR("https://leinelab.org")
