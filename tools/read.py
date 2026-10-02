"""veraltet"""
import sqlite3
from pathlib import Path
DB_PATH = Path(__file__).parent.parent / "game" / "auto-save.sqlite"
def connect():
    conn=sqlite3.connect(str(DB_PATH))
    cursor=conn.cursor()
    return conn, cursor
#conn, cursor = connect()
#cursor.execute('select * from runs')
#lists=cursor.fetchall()
#for row in lists:
#    print(" {} | {}".format(row[0], row[1]))



def delete():
    cursor.execute("DELETE FROM obstacles")
    cursor.execute("DELETE FROM runs")
    cursor.execute("DELETE FROM presses")



conn, cursor = connect()

###delete()
# cursor.execute('ALTER TABLE runs ADD COLUMN "run_nr" INTEGER')
conn.commit()
conn.close()