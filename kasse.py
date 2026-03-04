#!/usr/bin/env python3

import led, buzzer, scanner, tag, display, buttons, makerspaceapi, time, logging, settings

#PIN_SCANNER_ACTIVE  = 18
PIN_SCANNER_ACTIVE  = -1

scan = scanner.BarcodeScanner(PIN_SCANNER_ACTIVE, settings.serialport)
card = tag.NFCtag(port = 1)
disp = display.Display()
btns = buttons.Buttons(21, 20)
buzz = buzzer.Buzzer(19)
led  = led.LED(5, 13, 6)
api  = makerspaceapi.MakerSpaceAPI()
value = 0

def buttonLoop(timeout = 20, countdown_button = -1):
	tout = time.time() + timeout
	lsecs = -1
	btns.resetState()
	while tout > time.time():
		pressed = btns.getPressed()
		if pressed[1]: #cancel
			return 0
		if pressed[0]: #ok
			return 1
		if countdown_button != -1:
			csecs = int(tout - time.time())
			if csecs != lsecs:
				disp.showCountdown(countdown_button, csecs)
				lsecs = csecs
		time.sleep(0.1)
	logging.info("Waiting for buttons timed out")
	return -1

def showConnectUri():
	disp.dim(100)
	disp.showOIDCscan()
	cancel = time.time() + 10
	btns.resetState()
	uid = None
	while uid is None:
		uid = card.get()
		pressed = btns.getPressed()
		if time.time() > cancel or pressed[1]:
			return
	if uid == settings.uid_guest:
		disp.showOIDCfail()
		time.sleep(5)
		return
	url = api.getConnectLink(uid)
	if url:
		disp.showQR(url)
		buttonLoop()
	else:
		disp.showOIDCfail()
		time.sleep(5)

def ui():
	disp.showTag(settings.uid_guest is not None)
	uid = None
	idle = time.time() + 30
	led.clear()
	while uid is None:
		uid = card.get()
		if time.time() > idle:
			disp.dim(20)
		if uid is None:
			pressed = btns.getPressed()
			if pressed[0]:
				uid = settings.uid_guest
			elif pressed[1]:
				showConnectUri()
				return
	print(uid)
	disp.dim(100)
	if not api.ping():
		disp.showNoConnection()
		led.red()
		time.sleep(5)
		return

	cancel = 0
	value = api.getCard(uid)
	if value is None:
		disp.showTagNotKnown()
		led.red()
		if buttonLoop() == 1:
			uid2 = None
			timeout = time.time() + 10
			disp.showTagAgain()
			while uid2 is None and timeout > time.time():
				uid2 = card.get()
			if uid == uid2:
				if api.addCard(uid):
					value = 0
				else:
					disp.showRegisterFail()
					cancel = 1
					time.sleep(5)
			else:
				disp.showTagDifferent()
				cancel = 1
				time.sleep(5)
		else:
			cancel = 1

	while not cancel:
		buzz.beep(buzz.A5, 0.15)
		disp.showScan(value)
		led.white()
		bc = None
		retries = 0
		btns.resetState()
		timeout = time.time() + 10
		scan_iteration = 0
		while bc is None and timeout > time.time():
			bc = scan.scan(scan_iteration)
			scan_iteration += 1
			pressed = btns.getPressed()
			if pressed[1]:
				cancel = 1
				break
		scan.endScan()
		if cancel:
			break
		if bc == None:
			disp.showNoCode()
			led.blue()
			if buttonLoop() != 1:
				cancel = 1
		else:
			bc = api.getAlias(bc)
			product = api.getProduct(bc)
			if product is None:
				topupval, isused = api.checkTopUp(bc)
				if topupval == None:
					led.purple()
					disp.showNoProduct()
					if buttonLoop(10, 0) != 1:
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
						if buttonLoop(10, 0) != 1:
							cancel = 1
					elif b == -1:
						cancel = 1
					else:
						if api.topUpCard(uid, bc):
							led.green()
							value = api.getCard(uid)
							disp.showValue(value)
							led.blue()
							if buttonLoop(10) != 1:
								cancel = 1
						else:
							led.red()
						time.sleep(1)
			else:
				led.yellow()
				disp.showProduct(product['name'], product['price'], value)
				if product['price'] > value:
					buzz.abort()
				ret = buttonLoop(5, 1)
				if ret == 1 or ret == -1:
					if product['price'] <= value:
						api.buyProduct(uid, bc)
						value = api.getCard(uid)
						led.green()
						disp.showScanMore(value)
						if buttonLoop() != 1:
							cancel = 1
				else:
					if product['price'] > value:
						cancel = 1
					else:
						led.red()
						value = api.getCard(uid)
						disp.showScanMore(value)
						if not buttonLoop():
							cancel = 1
							led.red()
							time.sleep(1)

if __name__ == '__main__':
	while True:
		ui()
