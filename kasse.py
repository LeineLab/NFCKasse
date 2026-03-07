#!/usr/bin/env python3

import led, buzzer, scanner, tag, display, buttons, makerspaceapi, time, logging, settings
import i18n
from i18n import _

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

_languages = getattr(settings, 'languages', ['de'])
_lang_index = 0
i18n.load(_languages)
i18n.set_language(_languages[0])


def _lang_btn():
	"""Return the display name of the next language, or '' if only one language is configured."""
	if len(_languages) < 2:
		return ''
	return i18n.lang_name(_languages[(_lang_index + 1) % len(_languages)])


def _cycle_language():
	global _lang_index
	_lang_index = (_lang_index + 1) % len(_languages)
	i18n.set_language(_languages[_lang_index])


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
		disp.error(_('msg.already_connected'))
		time.sleep(5)

def ui():
	disp.message(_('msg.present_card'), _('btn.guest') if settings.uid_guest is not None else "", _lang_btn())
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
				_cycle_language()
				return
	print(uid)
	disp.dim(100)
	if not api.ping():
		disp.error(_('msg.no_connection'))
		led.red()
		time.sleep(5)
		return

	cancel = 0
	value, oidc = api.getCard(uid)
	if value is None:
		disp.info(_('msg.card_unknown'), _('btn.register'), _('btn.cancel'))
		led.red()
		if buttonLoop() == 1:
			# Verify, that the cards ID is consistent.
			# ID-/Bank-/Creditcards don't play well with the mifare ID readout.
			uid2 = None
			timeout = time.time() + 10
			disp.info(_('msg.present_again'))
			while uid2 is None and timeout > time.time():
				uid2 = card.get()
			if uid == uid2:
				if api.addCard(uid):
					value = 0
				else:
					disp.error(_('msg.register_failed'))
					cancel = 1
					time.sleep(5)
			else:
				# Do not register if card id is not consistent.
				disp.error(_('msg.card_id_mismatch'))
				cancel = 1
				time.sleep(5)
		else:
			cancel = 1

	while not cancel:
		buzz.beep(buzz.A5, 0.15)
		disp.message(_('msg.scan_item', balance=value), _('btn.connect') if not oidc and uid != settings.uid_guest else "", _('btn.logout'))
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
			disp.error(_('msg.no_barcode'), _('btn.scan'), _('btn.logout'))
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
					disp.error(_('msg.product_not_found'), _('btn.scan'), _('btn.logout'))
					if buttonLoop(10, 0) != 1:
						cancel = 1
				elif isused:
					led.red()
					disp.error(_('msg.topup_used'), _('btn.scan'), _('btn.logout'))
					if buttonLoop(10) != 1:
						cancel = 1
				else:
					led.yellow()
					disp.message(_('msg.topup_value', value=topupval), _('btn.topup'), _('btn.cancel'))
					b =  buttonLoop(10)
					if b == 0:
						disp.success(_('msg.more_items', balance=value), _('btn.scan'), _('btn.logout'))
						if buttonLoop(10, 0) != 1:
							cancel = 1
					elif b == -1:
						cancel = 1
					else:
						if api.topUpCard(uid, bc):
							led.green()
							value, oidc = api.getCard(uid)
							disp.message(_('msg.hello_balance', balance=value), _('btn.scan'), _('btn.logout'))
							led.blue()
							if buttonLoop(10) != 1:
								cancel = 1
						else:
							led.red()
						time.sleep(1)
			else:
				led.yellow()
				pname = product['name'].replace(' ', '\u00a0')
				if product['price'] > value:
					buzz.abort()
					disp.error(_('msg.product_detail', name=pname, price=product['price'], balance=value), _('btn.scan'), _('btn.cancel'))
				else:
					disp.message(_('msg.product_detail', name=pname, price=product['price'], balance=value), _('btn.buy'), _('btn.cancel'))
				ret = buttonLoop(5, 1)
				if ret == 1 or ret == -1:
					if product['price'] <= value:
						if api.buyProduct(uid, bc):
							value, oidc = api.getCard(uid)
							led.green()
							disp.success(_('msg.more_items', balance=value), _('btn.scan'), _('btn.logout'))
							buzz.beep(buzz.A6, 0.15)
						else:
							led.red()
							disp.error(_('msg.purchase_failed'), _('btn.scan'), _('btn.logout'))
							buzz.abort()
						if buttonLoop() != 1:
							cancel = 1
				else:
					if product['price'] > value:
						cancel = 1
					else:
						led.red()
						value, oidc = api.getCard(uid)
						disp.error(_('msg.other_items', balance=value), _('btn.scan'), _('btn.logout'))
						if not buttonLoop():
							cancel = 1
							led.red()
							time.sleep(1)

if __name__ == '__main__':
	while True:
		ui()
