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

BTN_GUEST    = "Gast"
BTN_SCAN     = "Artikel scannen"
BTN_LOGOUT   = "Logout"
BTN_CANCEL   = "Abbruch"
BTN_BUY      = "Kaufen"
BTN_REGISTER = "Registrieren"
BTN_CONNECT  = "OIDC verbinden"
BTN_LANGUAGE = "Language"

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

def showConnectUri(uid):
	url = api.getConnectLink(uid)
	if url:
		disp.showQR(url)
		buttonLoop()
	else:
		disp.error("Karte bereits\nverbunden?")
		time.sleep(5)

def ui():
	disp.message("Karte vorhalten", BTN_GUEST if settings.uid_guest is not None else "", BTN_LANGUAGE)
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
				# TODO: change language
				pass
	print(uid)
	disp.dim(100)
	if not api.ping():
		disp.error("Keine Verbindung\nAPI/WLAN offline\nGgf. neu starten")
		led.red()
		time.sleep(5)
		return

	cancel = 0
	value, oidc = api.getCard(uid)
	if value is None:
		disp.info("Karte unbekannt\nNeu registrieren?", BTN_REGISTER, BTN_CANCEL)
		led.red()
		if buttonLoop() == 1:
			# Verify, that the cards ID is consistent.
			# ID-/Bank-/Creditcards don't play well with the mifare ID readout.
			uid2 = None
			timeout = time.time() + 10
			disp.info("Karte erneut\nvorhalten")
			while uid2 is None and timeout > time.time():
				uid2 = card.get()
			if uid == uid2:
				if api.addCard(uid):
					value = 0
				else:
					disp.error("Registrierung\nfehlgeschlagen")
					cancel = 1
					time.sleep(5)
			else:
				# Do not register if card id is not consistent.
				disp.error("Karten-ID weicht ab\nKein Konto angelegt.")
				cancel = 1
				time.sleep(5)
		else:
			cancel = 1

	while not cancel:
		buzz.beep(buzz.A5, 0.15)
		disp.message("Artikel scannen\nDerzeitiges Guthaben:\n%.2f" % value, BTN_CONNECT if not oidc and uid != settings.uid_guest else "", BTN_LOGOUT)
		led.white()
		bc = None
		btns.resetState()
		timeout = time.time() + 10
		scan_iteration = 0
		while bc is None and timeout > time.time():
			bc = scan.scan(scan_iteration)
			scan_iteration += 1
			pressed = btns.getPressed()
			if pressed[0] and not oidc and uid != settings.uid_guest:
				showConnectUri()
			if pressed[1]:
				cancel = 1
				break
		scan.endScan()
		if cancel:
			break
		if bc == None:
			disp.error("Kein Barcode erkannt", BTN_SCAN, BTN_LOGOUT)
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
					disp.error("Produkt nicht gelistet", BTN_SCAN, BTN_LOGOUT)
					if buttonLoop(10, 0) != 1:
						cancel = 1
				elif isused:
					led.red()
					disp.error("Aufladecode bereits\nbenutzt. Aufladen\nnicht möglich", BTN_SCAN, BTN_LOGOUT)
					if buttonLoop(10) != 1:
						cancel = 1
				else:
					led.yellow()
					disp.message("Gegenwert:\n%.2f" % (topupval, ), "Aufladen", BTN_CANCEL)
					b =  buttonLoop(10)
					if b == 0:
						disp.success("Weitere Artikel?\nDerzeitiges Guthaben:\n%.2f", BTN_SCAN, BTN_LOGOUT)
						if buttonLoop(10, 0) != 1:
							cancel = 1
					elif b == -1:
						cancel = 1
					else:
						if api.topUpCard(uid, bc):
							led.green()
							value, oidc = api.getCard(uid)
							disp.message("Hallo!\nDerzeitiges Guthaben:\n%.2f" % value, BTN_SCAN, BTN_LOGOUT)
							led.blue()
							if buttonLoop(10) != 1:
								cancel = 1
						else:
							led.red()
						time.sleep(1)
			else:
				led.yellow()
				if product['price'] > value:
					buzz.abort()
					disp.error("Artikel:\n%s\nPreis: %.2f\nGuthaben: %.2f\n" % (product['name'], product['price'], value), BTN_SCAN, BTN_CANCEL)
				else:
					disp.message("Artikel:\n%s\nPreis: %.2f\nGuthaben: %.2f" % (product['name'], product['price'], value), BTN_BUY, BTN_CANCEL)
				ret = buttonLoop(5, 1)
				if ret == 1 or ret == -1:
					if product['price'] <= value:
						if api.buyProduct(uid, bc):
							value, oidc = api.getCard(uid)
							led.green()
							disp.success("Weitere Artikel?\nDerzeitiges Guthaben:\n%.2f" % value, BTN_SCAN, BTN_LOGOUT)
							buzz.beep(buzz.A6, 0.15)
						else:
							led.red()
							disp.error("Fehler beim Kauf!", BTN_SCAN, BTN_LOGOUT)
							buzz.abort()
						if buttonLoop() != 1:
							cancel = 1
				else:
					if product['price'] > value:
						cancel = 1
					else:
						led.red()
						value, oidc = api.getCard(uid)
						disp.error("Anderen Artikel?\nDerzeitiges Guthaben:\n%.2f", BTN_SCAN, BTN_LOGOUT)
						if not buttonLoop():
							cancel = 1
							led.red()
							time.sleep(1)

if __name__ == '__main__':
	while True:
		ui()
