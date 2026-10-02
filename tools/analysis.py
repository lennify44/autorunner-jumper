import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent / "game" / "auto-save.sqlite"
JUMP_LEAD = 0.2625      # muss zum Spiel passen
WINDOW = 0.35           # Zuordnungsfenster um den Sollzeitpunkt


def lade():
    conn = sqlite3.connect(DB_PATH)
    runs = pd.read_sql("SELECT * FROM runs", conn)
    presses = pd.read_sql("SELECT * FROM presses", conn)
    obstacles = pd.read_sql("SELECT * FROM obstacles", conn)
    conn.close()
    return runs, presses, obstacles

def ordne_zu(run_id, obstacles, presses):
    """Ordnet pro Hindernis nächstliegenden Druck zu"""
    obst = obstacles[obstacles.run_id == run_id].sort_values("beat_time") # alle obst
    prss = presses[(presses.run_id == run_id) & (presses.effektiv == 1)] # alle effektiven presses
    frei = sorted(prss.t_press) # freie presses

    row = []
    for _, o in obst.iterrows():
        t_ideal = o.beat_time - JUMP_LEAD
        kand = [p for p in frei if abs(p - t_ideal) <= WINDOW]
        best = min(kand, key=lambda p: abs(p - t_ideal)) if kand else None
        if best is not None:
            frei.remove(best)
        row.append({
            "run_id": run_id, "idx": o.idx, "beat_time": o.beat_time,
            "t_ideal": t_ideal, "t_press": best,
            "abweichung": None if best is None else best - t_ideal,
            "kollision": o.hit,
        })
    return pd.DataFrame(row)
runs, presses, obstacles = lade()
einzeln = pd.concat([ordne_zu(rid, obstacles, presses) for rid in runs.run_id],
                    ignore_index=True)
einzeln = einzeln.merge(
    runs[["run_nr", "run_id", "participant", "offset", "position", "calib_offset"]], on="run_id")

einzeln["korrigiert"] = einzeln.abweichung - einzeln.calib_offset.fillna(0.0)

per_run = einzeln.groupby(["run_nr", "run_id", "participant", "offset"]).agg(
    hindernisse=("idx", "count"),
    zugeordnet=("abweichung", "count"),
    median_ms=("korrigiert", lambda s: s.median() * 1000),
    streuung_ms=("korrigiert", lambda s: s.std() * 1000),
    kollisionen=("kollision", "sum"),
).reset_index()
per_run["ausgelassen"] = per_run.hindernisse - per_run.zugeordnet

print(per_run.to_string(index=False, float_format=lambda v: f"{v:.1f}"))
doppelt = per_run.groupby(["participant", "offset"]).size()
doppelt = doppelt[doppelt > 1]
if len(doppelt):
    print()
    print("Achtung, mehrfach erhoben:")
    print(doppelt.to_string())