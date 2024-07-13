# Kassennutzung

## Erste Einrichtung
Halte deinen NFC Tag (Mifare) an das Lesegerät.
Solltest du noch keine Karte haben, kannst du am Bankomaten eine neue kaufen.
Sofern dieser noch nicht im System registriert ist, wirst du gefragt, ob du deinen Tag neu anlegen möchtest.
Bitte benutze keinen Personalausweis, Kredit-/EC-Karte, da sich diese jedes Mal anders gegenüber dem System ausweisen, daher musst du deine Karte zwei Mal anhalten, um sicherzustellen, dass die ID gleich bleibt.
Studi-Ausweise hingegen funktionieren problemlos.

## Karte aufladen
### Bankomat
Halte deine registrierte Karte an den Bankomaten, wähle Getränkekasse und Einzahlung.
Scheine bis 50€ und Münzen ab 50ct werden akzeptiert.
### QR-Code
Tausche dein Geld beim Vorstand gegen einen QR-Code ein.
Lege deine registrierte Karte auf das Gerät und wähle "Artikel scannen".
Den erhaltenen QR-Code kannst du entweder auf einem Endgerät oder als Ausdruck vorzeigen und dann die Buchung mit "Aufladen" an der Kasse bestätigen.
Das eingetauschte Geld ist nun auf deinen Tag gebucht.

## Artikel kaufen
Halte deinen Tag an die Kasse, und halte das/die Produkte bereit, die du Buchen möchtest.
Wähle nach erfolgreicher Erfassung deines Tags "Artikel scannen" und halte nun das erste Produkt vor den Barcodescanner unter den Tasten.
Bei erfolgreichem Scan des Produkts wird der Preis angezeigt.
Bestätige den Kauf mit "Buchen" oder "Abbruch", wenn du dich dagegen entscheidest.
Weitere Artikel können nachfolgend wieder mit "Artikel scannen" erfasst werden.

Wenn du fertig bist, beende den Vorgang mit Logout.
Ansonsten wirst du nach kurzer Zeit automatisch ausgeloggt.

Produkte, die nicht mit Barcodes ausgestattet sind, haben neben der Kasse einen Ausdruck, der alternativ davor gehalten werden muss.

## Datenschutz
Die ID der Karte wird als Hash ohne persönliche Verbindung gespeichert, Transaktionen (Käufe, QR-Aufladungen, Überweisungen am Bankomaten) werden mit diesem Hash und einem Zeitstempel in Verbindung gespeichert.
Einzahlungen am Bankomaten werden dort zusätzlich mit der ungehashten ID gespeichert.

### Verlust der Karte
Da keine Zuordnung der Karten zu Personen erfolgt, ist eine Umbuchung oder Auszahlung einer verlorenen Karte nicht möglich.