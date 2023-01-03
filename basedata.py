import sqlite3, random, aiogram, config
from datetime import datetime

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
        '''Повертає рівень користувача по :scores:'''
        if scores <= 35:
            return "BEGINNER (A1)" 
        elif scores <= 49:
            return "PRE-INTERMEDIATE (A2)" 
        elif scores < 75:
            return "INTERMEDIATE (B1)"
        elif scores < 91:
            return "UPPER-INTERMEDIATE (B2)"
        else:
            return "ADVANCED (C1)"

    def get_user_info(self, user_id : int, data : str = '*'):
        with self.connection:
            return self.cursor.execute(f"SELECT {data} FROM Users WHERE user_id = {user_id}").fetchone()

    def get_new_game(self, level : str) -> tuple:
        '''Повертає найблищу гру по :level: користувача'''
        with self.connection:
            return self.cursor.execute("SELECT * FROM Games DESC WHERE level IN (?, 'All levels') AND is_started = 0 LIMIT 1", (level,)).fetchone()

    def get_list_users(self, game_code : int) -> list:
        '''Повертає список учасників гри по :game code:'''
        with self.connection:
            return [user_id for user_id, in self.cursor.execute("SELECT DISTINCT user_id FROM GameUsers WHERE game_code = ?", (game_code,)).fetchall()]

    def get_game_question(self, num_question : int, game_code : int) -> tuple | None:
        '''Повертає питання під номером N з БД по game_code'''
        with self.connection:
            try: return self.cursor.execute(f"SELECT * FROM GamesComponents WHERE game_code = '{game_code}'").fetchall()[num_question-1]
            except IndexError: return None

    def update_score(self, score : int, user_id : int, game_code : int):
        with self.connection:
            self.cursor.execute(f"UPDATE GameUsers SET score = score + {score} WHERE user_id = {user_id} AND game_code = '{game_code}'")
    
    def game_winner(self, game_code : int) -> tuple:
        with self.connection:
            return self.cursor.execute(f"SELECT user_id, Username, max(Score) FROM GameUsers WHERE game_code = '{game_code}'").fetchone()
    
    def reg_player(self, user_id : int, username : str, game_code : int):
        with self.connection:
            self.cursor.execute("INSERT INTO GameUsers VALUES (?, ?, 0, ?)", (user_id, game_code, username))
    @property
    def datetime_list(self):
        with self.connection:
            return [(datetime.strptime(_date,"%d.%m.%Y %H:%M"), game_code) for _date, game_code in self.cursor.execute("SELECT _date, game_code FROM Games")]

    def get_receivers_list(self, letters : str = ''):
        with self.connection:
            ls = [
                ('everyone', "Everyone", 'Everyone'),
                ('BEGINNER (A1)', "BEGINNER (A1)", 'BEGINNER (A1)'),
                ('PRE-INTERMEDIATE (A2)', "PRE-INTERMEDIATE (A2)", 'PRE-INTERMEDIATE (A2)'),
                ('INTERMEDIATE (B1)', "INTERMEDIATE (B1)", 'INTERMEDIATE (B1)'),
                ('UPPER-INTERMEDIATE (B2)', "UPPER-INTERMEDIATE (B2)", 'UPPER-INTERMEDIATE (B2)'),
                ('ADVANCED (C1)', "ADVANCED (C1)", 'ADVANCED (C1)')
            ]
            ls += self.cursor.execute(f"SELECT user_id, full_name, level FROM Users WHERE full_name LIKE '{letters}%' LIMIT 25").fetchall()
            return ls
    
    def get_receiver(self, type1 : str):
        if isinstance(type1, int) :
            print([(type1,)])
            return [(type1,)]
        with self.connection:
            ls = self.cursor.execute(f"""SELECT user_id FROM Users {'' if type1 == 'everyone' else f"WHERE level = '{type1}'"}""").fetchall()
            print(ls)
            return ls

    def get_higest_scores(self, game_code) -> dict:
        with self.connection:
            return dict(zip([str(i) for i, in self.cursor.execute(f"SELECT DISTINCT Score FROM GameUsers WHERE game_code = '{game_code}' ORDER BY Score DESC LIMIT 3").fetchall()], list(config.pos.values())))

    def get_game(self, game_code : str, args = '*'):
        with self.connection:
            return self.cursor.execute(f"SELECT {args} FROM Games WHERE game_code = '{game_code}'").fetchone()
    
    def get_questions(self, game_code : str, offset : str = ''):
        with self.connection:
            return [(question, optino)for question, optino in self.cursor.execute(f"SELECT question, options FROM GamesComponents WHERE game_code = '{game_code}' AND question LIKE '{offset}%' LIMIT 30").fetchall()]