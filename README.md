# coole readme

## externe Libraries

- pygame
- panda

#### Man sollte das nicht mit bluetooth wegen 150-250ms latenz spielen!

> Die Kalibrierung erfasst die Summe aus Systemlatenz und individueller Voreiligkeit. Da alle Sitzungen auf identischer Hardware mit kabelgebundenen Kopfhörern durchgeführt werden, ist der Systemanteil konstant und geht in den Bedingungsvergleich nicht ein. -claude 

## controls

### Menu

- zahlen eingeben für nummerierte testpersonen
- K für die Kalibrierung (bei jeder Person neu)
- Enter zum starten
- **ohne eingegebene Zahlen und ohne Kalibrierung kann man nicht starten**

### Game

- Leertaste zum springen

### break (so zwischen durchläufen)

- Enter für nächsten versuch

### analyse

- unter tools.
- ändert sich die spielphysik, muss JUMP_LEAD verändert werden.

## Einstellungen (config.toml)

- alle Konstanten (FPS, Physik, Offsets, Bluetooth, lustig-Modus, ...) stehen in `game/config.toml`, nicht mehr in game.py
- bei der exe liegt `config.toml` neben der exe; fehlt sie, wird sie beim Start mit den Standardwerten angelegt
- Tippfehler und falsche Werte zeigt das Spiel beim Start an

## exe bauen

- `pip install pyinstaller pygame-ce`, dann `pyinstaller autorunner.spec` -> `dist/Rhythmus-Autorunner.exe`
- Windows-exe nur auf Windows (oder in Wine) bauen, unter Linux kommt eine Linux-Datei raus
- die exe legt `auto-save.sqlite` neben sich an -> Messdaten von dort einsammeln

## code-expl/ (etc.)

- nur für die Erstellung wichtig -> irrelevant