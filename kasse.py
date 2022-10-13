#!/usr/bin/python3

import server, led, buzzer, scanner, tag, display, buttons, database, time, logging, settings
from threading import Thread

PIN_SCANNER_ACTIVE  = 18

scan = scanner.BarcodeScanner(PIN_SCANNER_ACTIVE, settings.serialport)
card = tag.NFCtag()
disp = display.Display()
btns = buttons.Buttons(21, 20)
buzz = buzzer.Buzzer(19)
led  = led.LED(5, 13, 6)
db = database.Database(
	host=settings.db_host,
	user=settings.db_user,
	password=settings.db_password,
	database=settings.db_database
)

app  = server.app
server.db = db
value = 0

def buttonLoop(timeout = 20):
	tout = time.time() + timeout
	btns.resetState()
	while tout > time.time():
		pressed = btns.getPressed()
		if pressed[1]: #cancel
			return 0
		if pressed[0]: #ok
			return 1
		time.sleep(0.1)
	logging.info("Waiting for buttons timed out")
	return -1

def worker():
	while True:
		ui()

def ui():
	disp.showTag()
	uid = None
	idle = time.time() + 30
	led.clear()
	while uid is None:
		uid = card.get()
		if time.time() > idle:
			disp.dim(20)
	print(uid)
	disp.dim(100)

	cancel = 0
	value = db.getCard(uid)
	if value is None:
		disp.showTagNotKnown()
		led.red()
		if buttonLoop() == 1:
			db.addCard(uid)
			value = 0
		else:
			cancel = 1

	if not cancel:
		led.blue()
		buzz.beep(buzz.A5, 0.15)
		disp.showValue(value)
		if buttonLoop() != 1:
			cancel = 1

	while not cancel:
		print("Scan")
		disp.showScan()
		led.white()
		bc = None
		retries = 0
		btns.resetState()
		while bc is None and retries < 10:
			bc = scan.scan()
			retries += 1
			pressed = btns.getPressed()
			if pressed[1]:
				cancel = 1
				break
		if cancel:
			break
		if bc == None:
			disp.showNoCode()
			led.blue()
			if buttonLoop() != 1:
				cancel = 1
		else:
			print(bc)
			name, price = db.getProduct(bc)
			if name is None:
				topupval, isused = db.checkTopUp(bc)
				if topupval == None:
					led.purple()
					disp.showNoProduct()
					if buttonLoop(10) != 1:
						cancel = 1
				elif isused:
					led.red()
					disp.showTopUpUsed()
					if buttonLoop(10) != 1:
						cancel = 1
				else:
					led.yellow()
					disp.showTopUp(topupval)
					b =  buttonLoop(10)
					if b == 0:
						disp.showScanMore()
						if buttonLoop(10) != 1:
							cancel = 1
					elif b == -1:
						cancel = 1
					else:
						if db.topUpCard(uid, bc):
							led.green()
							value = db.getCard(uid)
							disp.showValue(value)
							led.blue()
							if buttonLoop(10) != 1:
								cancel = 1
						else:
							led.red()
						time.sleep(1)
			else:
				led.yellow()
				disp.showProduct(name, price, value)
				if price > value:
					buzz.abort()
				ret = buttonLoop(10)
				if ret == 1:
					if price <= value:
						print(db.changeCardValue(uid, -price))
						print(db.reduceProductStock(bc, 1))
						value = db.getCard(uid)
						led.green()
						disp.showScanMore()
						if buttonLoop() != 1:
							cancel = 1
				elif ret == -1:
					cancel = 1
					led.red()
					time.sleep(1)
				else:
					if price > value:
						cancel = 1
					else:
						led.red()
						disp.showScanMore()
						if not buttonLoop():
							cancel = 1
							led.red()
							time.sleep(1)

thread = Thread(target=worker)
thread.daemon = True
thread.start()

server.app.run(host='0.0.0.0', threaded=True)
