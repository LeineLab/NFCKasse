# NFC Getränkekasse

Die NFC-Getränkekasse (flexibel natürlich auch für anderes einsetzbar) ist eine Self-Checkout Kasse für den Maker- und HackerSpace.

Für mehr Self-Service haben wir zusätzlich noch einen Bankautomaten gebaut, an dem die Tags eigenständig mit Bargeld aufgeladen werden können und die Transaktionshistorie eingesehen werden kann.
Gäste können einen aushängenden Tag nutzen, der vorher dann am Automaten aufgeladen werden kann.

Das Projekt basiert auf der [MakerSpaceAPI](https://github.com/LeineLab/MakerSpaceAPI) und nutzt die Kontenverwaltung.
- An der NFC-Kasse kann ein NFC-Token registriert werden, wie auch mit einem OIDC-Konto verknüpft werden (optional, sofern vorhanden, ansonsten anonyme Nutzung möglich).
- Produkte können erworben werden (Barcodescanner).
- Die Bestandslisten und sonstige Produktpflege wird über das Webinterface der API erledigt.

## Vorbereitungen
Benötigte Hardware:
- ILI9341 TFT
- GM65 Barcode-Leser
- PN532 NFC-Reader auf I2C konfiguriert
- Zwei Taster
- Raspberry Pi Zero 2 W (alternativ auch ein normaler Pi mit Ethernet oder WLAN; Zero erster Generation ist teils sehr langsam)

## Installation
Das Projekt wurde auf die [MakerSpaceAPI](https://github.com/LeineLab/MakerSpaceAPI) migriert, dafür zunächst einen Server einrichten.

Die `install.sh` ist für Raspberry Pis mit Debian Trixie ausgelegt.

### Notwendige Änderungen für >= Bookworm
Mit neueren Versionen, wie bookworm muss einerseits lgpio als Paket installiert werden, zusätzlich der Chip-Select Pin freigegeben werden.
`/boot/firmware/config.txt`:

`dtoverlay=spi0-0cs`

Beim Raspberry im reinen WLAN Betrieb geht dieses ohne externen Zugriff ab und zu in den Schlafmodus.
Das Webinterface ist dann nicht mehr erreichbar.
Nach jedem Neustart daher `/sbin/iw wlan set power_save off` ausführen, etwa in einem crontab per `@reboot`.
Bei Trixie-Installationen lässt sich der Power-Down auch in der `raspi-config` deaktivieren.
