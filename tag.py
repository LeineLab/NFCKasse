#!/usr/bin/env python3

from pn532pi import Pn532I2c, Pn532

import time

import nfc_poller


class NFCtag:
    def __init__(self, port=1, uid_hash=True):
        self.i2c = Pn532I2c(port)
        self.nfc = Pn532(self.i2c)
        self.nfc.begin()
        self.nfc.setPassiveActivationRetries(nfc_poller.ACTIVATION_RETRIES)
        self.nfc.SAMConfig()
        self.poller = nfc_poller.NfcPoller(self.nfc)
        self.poller.start()

    """Check if there is a tag available and return hash if present
	"""

    def get(self):
        uid = self.poller.get_int()
        if uid is None:
            # The poller never blocks; keep callers' busy loops from spinning.
            time.sleep(0.02)
        return uid


if __name__ == "__main__":
    oldTag = None
    nfctag = NFCtag()
    while True:
        tag = nfctag.get()
        if tag != oldTag:
            oldTag = tag
            if tag is not None:
                print("Found new Tag: %s" % tag)
