import RPi.GPIO as GPIO

class Buttons:
	btn_ok = None
	btn_cancel = None
	pressed_ok = 0
	pressed_cancel = 0
	var = 0

	def __pressed(channel):
		if channel == Buttons.btn_ok:
			Buttons.pressed_ok = 1
		if channel == Buttons.btn_cancel:
			Buttons.pressed_cancel = 1

	def __setupGPIO(self, gpio):
		GPIO.setup(gpio, GPIO.IN, GPIO.PUD_UP)
		GPIO.add_event_detect(gpio, GPIO.FALLING, callback=Buttons.__pressed, bouncetime=50)

	def __init__(self, ok, cancel):
		GPIO.setmode(GPIO.BCM)
		Buttons.btn_ok = ok
		Buttons.btn_cancel = cancel
		self.__setupGPIO(ok)
		self.__setupGPIO(cancel)

	def resetState(self):
		Buttons.pressed_ok = 0
		Buttons.pressed_cancel = 0

	def getPressed(self):
		ret = (Buttons.pressed_ok, Buttons.pressed_cancel)
		Buttons.pressed_ok = 0
		Buttons.pressed_cancel = 0
		return ret

if __name__ == '__main__':
	from time import sleep
	btns = Buttons(20, 21)
	while 1:
		print(btns.getPressed())
		sleep(1)
