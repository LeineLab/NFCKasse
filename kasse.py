#!/usr/bin/env python3

import led, buzzer, scanner, tag, display, buttons, makerspaceapi, time, logging, settings
import i18n
from i18n import _

# PIN_SCANNER_ACTIVE  = 18
PIN_SCANNER_ACTIVE = -1

scan = scanner.BarcodeScanner(PIN_SCANNER_ACTIVE, settings.serialport)
card = tag.NFCtag(port=1)
disp = display.Display()
btns = buttons.Buttons(21, 20)
buzz = buzzer.Buzzer(19)
led = led.LED(5, 13, 6)
api = makerspaceapi.MakerSpaceAPI()
value = 0

_languages = getattr(settings, "languages", ["de"])
_lang_index = 0
i18n.load(_languages)
i18n.set_language(_languages[0])

RIGHT_BUTTON = 1
LEFT_BUTTON = 0
NO_BUTTON = -1


def _lang_btn():
    """Return the display name of the next language, or '' if only one language is configured."""
    if len(_languages) < 2:
        return ""
    return i18n.lang_name(_languages[(_lang_index + 1) % len(_languages)])


def _cycle_language():
    global _lang_index
    _lang_index = (_lang_index + 1) % len(_languages)
    i18n.set_language(_languages[_lang_index])


def buttonLoop(timeout: int = 20, countdown_button: int = NO_BUTTON):
    tout = time.time() + timeout
    lsecs = -1
    btns.resetState()
    while tout > time.time():
        pressed = btns.getPressed()
        if pressed[RIGHT_BUTTON]:  # cancel
            return RIGHT_BUTTON
        if pressed[LEFT_BUTTON]:  # ok
            return LEFT_BUTTON
        if countdown_button != -1:
            csecs = int(tout - time.time())
            if csecs != lsecs:
                disp.showCountdown(countdown_button, csecs)
                lsecs = csecs
        time.sleep(0.1)
    logging.info("Waiting for buttons timed out")
    return countdown_button


def showConnectUri(uid: int):
    url = api.getConnectLink(uid)
    if url:
        disp.showQR(url)
        # Allow for any button press to quit
        buttonLoop()
    else:
        disp.error(_("msg.already_connected"))
        # Allow for any button press to quit
        buttonLoop(5)


def createAccount(uid: int):
    disp.info(_("msg.card_unknown"), _("btn.register"), _("btn.cancel"))
    led.red()
    if buttonLoop() == LEFT_BUTTON:
        # Verify, that the cards ID is consistent.
        # ID-/Bank-/Creditcards don't play well with the mifare ID readout.
        uid2 = None
        timeout = time.time() + 10
        disp.info(_("msg.present_again"))
        while uid2 is None and timeout > time.time():
            uid2 = card.get()
        if uid == uid2:
            if api.addCard(uid):
                return True
            else:
                disp.error(_("msg.register_failed"))
                # Allow for any button press to quit
                buttonLoop(5)
                return False
        else:
            # Do not register if card id is not consistent.
            disp.error(_("msg.card_id_mismatch"))
            # Allow for any button press to quit
            buttonLoop(5)
            return False
    else:
        return False


def buyProduct(uid: int, value: float, product):
    led.yellow()
    pname = product["name"].replace(" ", "\u00a0")
    if product["price"] > value:
        buzz.abort()
        disp.error(
            _("msg.product_detail", name=pname, price=product["price"], balance=value),
            _("btn.scan"),
            _("btn.logout"),
        )
        return buttonLoop() == LEFT_BUTTON
    else:
        disp.message(
            _("msg.product_detail", name=pname, price=product["price"], balance=value),
            _("btn.buy"),
            _("btn.cancel"),
        )
    if buttonLoop(5, 1) == LEFT_BUTTON:
        if product["price"] <= value:
            if api.buyProduct(uid, product["ean"]):
                value, oidc = api.getCard(uid)
                led.green()
                disp.success(
                    _("msg.more_items", balance=value), _("btn.scan"), _("btn.logout")
                )
                buzz.beep(buzz.A6, 0.15)
            else:
                led.red()
                disp.error(_("msg.purchase_failed"), _("btn.scan"), _("btn.logout"))
                buzz.abort()
            if buttonLoop() != LEFT_BUTTON:
                return False
    else:
        if product["price"] > value:
            return False
        else:
            led.red()
            value, oidc = api.getCard(uid)
            disp.error(
                _("msg.purchase_cancel", balance=value), _("btn.scan"), _("btn.logout")
            )
            if buttonLoop() != LEFT_BUTTON:
                led.red()
                time.sleep(1)
                return False
    return True


def ui():
    disp.message(
        _("msg.present_card"),
        _("btn.guest") if settings.uid_guest is not None else "",
        _lang_btn(),
    )
    uid = None
    idle = time.time() + 30
    led.clear()
    while uid is None:
        uid = card.get()
        if time.time() > idle:
            disp.dim(20)
        if uid is None:
            pressed = btns.getPressed()
            if pressed[LEFT_BUTTON]:
                uid = settings.uid_guest
            elif pressed[RIGHT_BUTTON]:
                _cycle_language()
                return
    print(uid)
    disp.dim(100)
    if not api.ping():
        disp.error(_("msg.no_connection"))
        led.red()
        # Allow for any button press to quit
        buttonLoop(5)
        return

    cancel = 0
    value, oidc = api.getCard(uid)
    if value is None:
        if createAccount(uid):
            value, oidc = api.getCard(uid)
        else:
            return

    while True:
        buzz.beep(buzz.A5, 0.15)
        disp.message(
            _("msg.scan_item", balance=value),
            _("btn.connect") if (not oidc and uid != settings.uid_guest) else "",
            _("btn.logout"),
        )
        led.white()
        bc = None
        btns.resetState()
        timeout = time.time() + 10
        scan_iteration = 0
        while bc is None and timeout > time.time():
            bc = scan.scan(scan_iteration)
            scan_iteration += 1
            pressed = btns.getPressed()
            if pressed[LEFT_BUTTON] and not oidc and uid != settings.uid_guest:
                scan.endScan()
                # Show barcode
                showConnectUri(uid)
                # Quit session
                return
            if pressed[RIGHT_BUTTON]:  # Logout
                scan.endScan()
                return
        scan.endScan()
        if cancel:
            break
        if bc == None:
            disp.error(_("msg.no_barcode"), _("btn.scan"), _("btn.logout"))
            led.blue()
            if buttonLoop() != LEFT_BUTTON:
                return
        else:
            bc = api.getAlias(bc)
            product = api.getProduct(bc)
            if product:
                if not buyProduct(uid, value, product):
                    break
            if product is None:
                led.purple()
                disp.error(_("msg.product_not_found"), _("btn.scan"), _("btn.logout"))
                if buttonLoop(10, 0) != LEFT_BUTTON:
                    return
                """
				# Currently not in use, as with the switch from database to MakerSpaceAPI there is currently no topup code
				topupval, isused = api.checkTopUp(bc)
				if topupval == None:
					led.purple()
					disp.error(_('msg.product_not_found'), _('btn.scan'), _('btn.logout'))
					if buttonLoop(10, 0) != LEFT_BUTTON:
						return
				elif isused:
					led.red()
					disp.error(_('msg.topup_used'), _('btn.scan'), _('btn.logout'))
					if buttonLoop(10) != LEFT_BUTTON:
						return
				else:
					led.yellow()
					disp.message(_('msg.topup_value', value=topupval), _('btn.topup'), _('btn.cancel'))
					b =  buttonLoop(10)
					if b == RIGHT_BUTTON:
						disp.success(_('msg.more_items', balance=value), _('btn.scan'), _('btn.logout'))
						if buttonLoop(10, 0) != LEFT_BUTTON:
							return
					elif b == NO_BUTTON:
						return
					else:
						if api.topUpCard(uid, bc):
							led.green()
							value, oidc = api.getCard(uid)
							disp.message(_('msg.hello_balance', balance=value), _('btn.scan'), _('btn.logout'))
							led.blue()
							if buttonLoop(10) != LEFT_BUTTON:
								return
						else:
							led.red()
						time.sleep(1)
				"""


if __name__ == "__main__":
    while True:
        ui()
