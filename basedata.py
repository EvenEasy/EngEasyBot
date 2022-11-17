import sqlite3, typing

class BaseData:
    def __init__(self, filename):
        self.connection = sqlite3.connect(filename)
        self.cursor = self.connection.cursor()

    def sqlite(self, sql : str):
        with self.connection:
            return self.cursor.execute(sql).fetchall()
    def sqlite1(self, sql : str, params):
        with self.connection:
            return self.cursor.execute(sql, params).fetchall()

    def get_hight_id(self) -> int:
        with self.connection:
            return self.cursor.execute("SELECT MAX(id) FROM Questions").fetchone()[0]

    def get_question(self,level : int | str, num : int):
        with self.connection:
            return self.cursor.execute(f"""SELECT id, question, level, scores, options, file FROM Questions WHERE level = {level} ORDER BY id""").fetchall()[num-2]

    def get_level(self, scores) -> str:
        if scores <= 29:
            return "BEGINNER (A1)" 
        elif scores <= 49:
            return "PRE-INTERMEDIATE (A2)" 
        elif scores <= 69:
            return "INTERMEDIATE (B1)"
        elif scores <= 89:
            return "UPPER-INTERMEDIATE (B2)"
        else:
            return "ADVANCED (C1)"
