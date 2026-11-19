"""liest config.toml und sagt, wo die dateien liegen -- egal ob als game.py oder als exe gestartet"""
import shutil
import sys
import tomllib
import traceback
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)  # True, wenn als exe (PyInstaller) gestartet
# APP_DIR: config und db liegen neben der exe, sonst landen die messdaten im temp-ordner und sind weg
APP_DIR = Path(sys.executable).parent if FROZEN else Path(__file__).parent
# BUNDLE_DIR: was in die exe eingepackt ist (musik, standard-config); als game.py einfach der ordner hier
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
CONFIG_PATH = APP_DIR / "config.toml"
DEFAULT_CONFIG_PATH = BUNDLE_DIR / "config.toml"

POSITIV = ["WIDTH", "HEIGHT", "FPS", "SCROLL_SPEED", "JUMP_VELOCITY", "GRAVITY", "BPM", "SLOT_BEATS"]


class ConfigError(Exception):
    pass


class Config(dict):
    def __missing__(self, key):
        raise ConfigError(f"{key} fehlt in {CONFIG_PATH}")


if FROZEN:
    # in der exe schliesst sich das konsolenfenster bei einem absturz sofort -> fehler stehen lassen
    def _fehler_anzeigen(typ, wert, tb):
        if "pygame" in sys.modules:
            sys.modules["pygame"].quit()
        if issubclass(typ, ConfigError):
            print(f"Fehler in der config: {wert}")
        else:
            traceback.print_exception(typ, wert, tb)
        input("\nEnter zum Beenden")
    sys.excepthook = _fehler_anzeigen


def _lesen(path):
    """gibt (werte, lustig) zurueck; die abschnitte ausser [lustig] sind nur zur ordnung da"""
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        raise ConfigError(f"{path} kaputt: {e}") from None
    werte = {}
    for abschnitt, inhalt in data.items():
        if abschnitt == "lustig":
            continue
        if isinstance(inhalt, dict):
            werte.update(inhalt)
        else:
            werte[abschnitt] = inhalt  # wert ganz oben ohne abschnitt geht auch
    return werte, data.get("lustig")


def _passt(wert, vorlage):
    """gibt den wert im typ der vorlage zurueck oder None, wenn er nicht passt"""
    if isinstance(vorlage, bool) or isinstance(wert, bool):  # bool ist in python auch ein int
        return wert if type(wert) is type(vorlage) else None
    if isinstance(vorlage, int):
        if isinstance(wert, float) and wert.is_integer():
            wert = int(wert)  # 120.0 ist auch ok
        return wert if isinstance(wert, int) else None
    if isinstance(vorlage, float):
        return float(wert) if isinstance(wert, (int, float)) else None
    if isinstance(vorlage, list):
        if not isinstance(wert, list) or not wert:
            return None
        liste = [_passt(w, vorlage[0]) for w in wert]
        return None if None in liste else liste
    return wert if isinstance(wert, type(vorlage)) else None


def _toml(wert):
    """so wie man es in die config schreibt: false statt False, "text" statt 'text'"""
    if isinstance(wert, bool):
        return str(wert).lower()
    if isinstance(wert, str):
        return f'"{wert}"'
    return repr(wert)


def _pruefen(werte, defaults):
    for key, wert in werte.items():
        if key not in defaults:
            raise ConfigError(f"unbekannte Einstellung {key} (Tippfehler?)")
        neu = _passt(wert, defaults[key])
        if neu is None:
            raise ConfigError(f"{key} = {_toml(wert)} passt nicht, Beispiel fuer einen gueltigen Wert: {_toml(defaults[key])}")
        werte[key] = neu


def load():
    """standardwerte aus der eingebauten config, darueber die config neben der exe"""
    if not CONFIG_PATH.exists():
        try:
            shutil.copyfile(DEFAULT_CONFIG_PATH, CONFIG_PATH)
            print(f"neue config angelegt: {CONFIG_PATH}")
        except OSError as e:
            print(f"konnte {CONFIG_PATH} nicht anlegen ({e}), nehme die standardwerte")
    defaults, default_lustig = _lesen(DEFAULT_CONFIG_PATH)
    werte, lustig = _lesen(CONFIG_PATH) if CONFIG_PATH.exists() else ({}, None)
    if lustig is None:
        lustig = default_lustig or {}  # ohne [lustig]-abschnitt gelten die eingebauten
    _pruefen(werte, defaults)
    _pruefen(lustig, defaults)

    cfg = Config({**defaults, **werte})
    if cfg["LUSTIG"]:
        cfg.update(lustig)

    for key in POSITIV:
        if cfg[key] <= 0:
            raise ConfigError(f"{key} muss groesser als 0 sein")
    if min(cfg["GAP_CHOICES"]) <= 0:
        raise ConfigError("GAP_CHOICES darf nur Zahlen groesser als 0 enthalten")
    if cfg["JUMP_VELOCITY"] ** 2 < 2 * cfg["GRAVITY"] * cfg["OBSTACLE_H"]:
        raise ConfigError("Sprung zu niedrig: mit JUMP_VELOCITY und GRAVITY kommt die Figur nicht ueber OBSTACLE_H")
    return cfg


def find_file(name):
    """datei neben der exe nehmen, sonst die eingebaute"""
    eigene = APP_DIR / name
    return eigene if eigene.exists() else BUNDLE_DIR / name
