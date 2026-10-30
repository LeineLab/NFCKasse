#!/opt/kasse/venv/bin/python3
"""
MakerSpaceAPI client for NFCKasse.

Configure via settings.py:
    api_url   = 'http://localhost:8000'
    api_token = '<checkout-box machine Bearer token>'
"""

import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# One shared session: HTTP keep-alive reuses the TCP/TLS connection between calls
# instead of a full handshake per request. If the server (or nginx) closed the idle
# connection, urllib3 reconnects: connect errors are retried for every method, read
# errors only for idempotent ones (GET/PUT/DELETE), so a POST whose response got lost
# is never sent twice.
_http = requests.Session()
_retry = Retry(total=1, connect=1, read=1, status=0, redirect=0, other=0, backoff_factor=0)
_http.mount("http://", HTTPAdapter(max_retries=_retry))
_http.mount("https://", HTTPAdapter(max_retries=_retry))
import settings

import logging

logger = logging.getLogger(__name__)


def _headers():
    return {"Authorization": f"Bearer {settings.api_token}"}


def _base():
    return settings.api_url.rstrip("/") + "/api/v1"


class MakerSpaceAPI:
    """REST API client for the NFCKasse checkout hardware."""

    def __init__(self, **kwargs):
        pass

    def ping(self):
        try:
            r = _http.get(
                f"{_base()}/products",
                headers=_headers(),
                timeout=3,
            )
            return r.ok
        except requests.RequestException:
            return False

    # ------------------------------------------------------------------ #
    # Card / user operations                                               #
    # ------------------------------------------------------------------ #

    def addCard(self, uid):
        """Register a new NFC card (uid is a raw integer)."""
        try:
            r = _http.post(
                f"{_base()}/users",
                headers=_headers(),
                json={"id": uid},
                timeout=5,
            )
            return r.ok
        except requests.RequestException:
            logger.exception("addCard failed")
            return False

    def getCard(self, uid):
        """Return balance for card uid, or None if not registered."""
        try:
            r = _http.get(
                f"{_base()}/users/nfc/{uid}",
                headers=_headers(),
                timeout=5,
            )
            if r.ok:
                return (
                    round(float(r.json().get("balance", 0)), 2),
                    r.json().get("oidc_sub", None) is not None,
                )
            if r.status_code == 404:
                return None, False
            return None, False
        except requests.RequestException:
            logger.exception("getCard failed")
            return None, False

    # ------------------------------------------------------------------ #
    # Product operations                                                   #
    # ------------------------------------------------------------------ #

    def getAlias(self, ean):
        """Resolve an alias EAN to the primary product EAN."""
        try:
            r = _http.get(
                f"{_base()}/products/{ean}",
                headers=_headers(),
                timeout=5,
            )
            if r.ok:
                return r.json().get("ean", ean)
            return ean
        except requests.RequestException:
            return ean

    def getProduct(self, ean):
        """Return product dict {ean, name, price, stock} or None."""
        try:
            r = _http.get(
                f"{_base()}/products/{ean}",
                headers=_headers(),
                timeout=5,
            )
            if r.ok:
                d = r.json()
                return {
                    "ean": d.get("ean"),
                    "name": d.get("name"),
                    "price": float(d.get("price", 0)),
                    "stock": d.get("stock"),
                }
            return None
        except requests.RequestException:
            logger.exception("getProduct failed")
            return None

    def getProducts(self):
        """Return list of all active products (sorted by category, name)."""
        try:
            r = _http.get(
                f"{_base()}/products",
                headers=_headers(),
                timeout=5,
            )
            if r.ok:
                products = []
                for d in r.json():
                    products.append(
                        {
                            "ean": d.get("ean"),
                            "name": d.get("name"),
                            "price": float(d.get("price", 0)),
                            "stock": d.get("stock"),
                            "category": d.get("category"),
                        }
                    )
                return products
        except requests.RequestException:
            logger.exception("getProducts failed")
        return []

    def buyProduct(self, uid, ean):
        """Deduct product price from card, reduce stock, record transaction."""
        try:
            r = _http.post(
                f"{_base()}/products/{ean}/purchase",
                headers=_headers(),
                json={"nfc_id": uid},
                timeout=5,
            )
            return (r.ok, r.json().get("detail"))
        except requests.RequestException:
            logger.exception("buyProduct failed")
            return (False, "Request failed")

    def getConnectLink(self, uid):
        """Generate a short-lived OIDC linking URL for a card.
        Returns the URL string, or None on error or if already linked (409)."""
        try:
            r = _http.post(
                f"{_base()}/users/{uid}/connect-link",
                headers=_headers(),
                timeout=5,
            )
            if r.ok:
                return r.json().get("url")
            if r.status_code == 409:
                return None  # already linked
            return None
        except requests.RequestException:
            logger.exception("getConnectLink failed")
            return None

    # ------------------------------------------------------------------ #
    # Topup codes - not yet supported in MakerSpaceAPI                   #
    # ------------------------------------------------------------------ #

    def checkTopUp(self, code):
        """Topup codes are not supported in MakerSpaceAPI. Returns (None, None)."""
        return None, None

    def topUpCard(self, uid, code):
        """Topup codes are not supported in MakerSpaceAPI. Returns False."""
        return False
