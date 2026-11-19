# Bauplan fuer die exe:  pyinstaller autorunner.spec   ->  dist/Rhythmus-Autorunner(.exe)
# Eingepackt werden Musik und config.toml (als Standardwerte). Beim ersten Start legt die exe
# config.toml und auto-save.sqlite neben sich an -- dort werden sie auch bearbeitet bzw. gesammelt.
import os

a = Analysis(
    [os.path.join(SPECPATH, "game", "game.py")],
    datas=[
        (os.path.join(SPECPATH, "game", "game_music.wav"), "."),
        (os.path.join(SPECPATH, "game", "config.toml"), "."),
    ],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="Rhythmus-Autorunner",
    console=True,  # Konsole zeigt "gespeichert: run ..." und Fehlermeldungen
    upx=False,
)
