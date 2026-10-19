from pathlib import Path
import sqlite3
from zapolnitel_bd import fill_hse_nn_database


def init_db(db_name = "NNNewsDB", schema_path="schema.sql"):
    file_path = Path(db_name+".sqlite")
    if file_path.is_file():
        print("BD exists ... OK")
        return 0
    else:
        print("BD exists ... NO")
        with open(schema_path, encoding="utf-8") as f:
            schema = f.read()
        conn = sqlite3.connect(db_name+".sqlite")
        conn.executescript(schema)
        conn.close()
        fill_hse_nn_database()
        if file_path.is_file():
            print("BD create ... OK")
            return 0
        else:
            print("BD create ... NO")
            return -1
