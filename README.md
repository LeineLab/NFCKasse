# NFC Getränkekasse

Die NFC Getränkekasse (flexibel natürlich auch für anderes einsetzbar) ist eine Self-Checkout Kasse für den Maker- und HackerSpace.
Standalone bietet sie die folgenden Funktionen:
- Registrierung neuer NFC-Tags (anonym)
- Kaufen von Artikeln mit EAN/QR-Code aus Guthaben
- Webverwaltung
    - 2FA via OTP (derzeit zwingend)
    - Artikelverwaltung (Bestand, Preis, ...)
    - Ausstellen von QR-Codes für Guthabenaufladungen (Single Use Token)

Für mehr Self-Service haben wir zusätzlich noch einen Bankautomaten gebaut, an dem die Tags eigenständig mit Bargeld aufgeladen werden können und die Transaktionshistorie eingesehen werden kann.
Gäste können einen aushängenden Tag nutzen, der vorher dann am Automaten aufgeladen werden kann.

## Vorbereitungen
Benötigte Hardware:
- ILI9341 TFT
- GM65 Barcode-Leser
- PN532 NFC-Reader auf I2C konfiguriert
- Zwei Taster
- Raspberry Pi Zero 2 W (alternativ auch ein normaler Pi mit Ethernet oder WLAN; Zero erster Generation ist teils sehr langsam)
    - Netzwerk ist neben der Installation hauptsächlich für die Warenwirtschaft (Artikel anlegen, Mengen anpassen, Preise aktualisieren) und das Generieren von Aufladecodes notwendig.

## Installation
Für die Datenhaltung muss eine MySQL Datenbank eingerichtet werden (`mariadb-server`).
Die restliche Installation funktioniert mit der Installation von `python-venv`:

```
apt install mariadb-server python-venv git
git clone [dieses git repo] kasse
cd kasse
python -m venv venv
venv/bin/pip install -r requirements.txt
cp settings.py.example settings.py
```

Nachfolgend muss ein User in der Datenbank angelegt werden und die Datenbank selbst erstellt werden.
```
sudo mysql
CREATE USER nfckasse@localhost IDENTIFIED BY [passwort];
CREATE DATABASE nfckasse;
GRANT SELECT, INSERT, UPDATE ON nfckasse.* TO nfckasse@localhost;
```
Statt `nfckasse` können als User und Datenbankname auch andere Namen genutzt werden.
Die Parameter dann entsprechend in die settings.py eintragen.
Um die Tabellen anzulegen reicht dann `sudo mysql -p nfckasse < nfc_kasse.sql`.

Wenn die `install.sh` genutzt wird, muss die Datenbank dennoch vorher angelegt, wie auch die `settings.py` angepasst werden!

### Notwendige Änderungen für >= Bookworm
Mit neueren Versionen, wie bookworm muss einerseits lgpio als Paket installiert werden, zusätzlich der Chip-Select Pin freigegeben werden.
`/boot/firmware/config.txt`:

`dtoverlay=spi0-0cs`

Beim Raspberry im reinen WLAN Betrieb geht dieses ohne externen Zugriff ab und zu in den Schlafmodus.
Das Webinterface ist dann nicht mehr erreichbar.
Nach jedem Neustart daher `/sbin/iw wlan set power_save off` ausführen, etwa in einem crontab per `@reboot`.