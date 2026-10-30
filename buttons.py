#!/usr/bin/env python3

import threading
import time

import RPi.GPIO as GPIO

# A press only counts if the button was released for at least this long before
# (filters contact bounce on release and a button that is still held down).
RELEASE_STABLE_S = 0.05
# A press that nobody collected for this long belongs to an old screen.
PRESS_MAX_AGE_S = 1.0


class Buttons:
    def __init__(self, ok, cancel):
        GPIO.setmode(GPIO.BCM)
        self._lock = threading.Lock()
        self._pins = {ok: "ok", cancel: "cancel"}
        self._pressed_at = {ok: None, cancel: None}
        self._released_at = {}
        for pin in self._pins:
            GPIO.setup(pin, GPIO.IN, GPIO.PUD_UP)
            # Both edges: the release time is needed to reject bounce and held buttons.
            self._released_at[pin] = (
                time.monotonic() - 1 if GPIO.input(pin) else None
            )
            GPIO.add_event_detect(pin, GPIO.BOTH, callback=self._edge, bouncetime=5)
        self._ok = ok
        self._cancel = cancel

    def _edge(self, pin):
        now = time.monotonic()
        level = GPIO.input(pin)
        with self._lock:
            if level:
                self._released_at[pin] = now
            else:
                rel = self._released_at[pin]
                if rel is not None and now - rel >= RELEASE_STABLE_S:
                    self._pressed_at[pin] = now
                # Needs a fresh release before the next press, whether accepted or not
                self._released_at[pin] = None

    def resetState(self):
        """Drop uncollected presses (a held button stays blocked until released)."""
        with self._lock:
            for pin in self._pressed_at:
                self._pressed_at[pin] = None

    def getPressed(self):
        now = time.monotonic()
        ret = []
        with self._lock:
            for pin in (self._ok, self._cancel):
                t = self._pressed_at[pin]
                self._pressed_at[pin] = None
                ret.append(1 if t is not None and now - t <= PRESS_MAX_AGE_S else 0)
        return tuple(ret)


if __name__ == "__main__":
    from time import sleep

    btns = Buttons(20, 21)
    while 1:
        print(btns.getPressed())
        sleep(1)
