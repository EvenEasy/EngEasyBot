TOKEN = "5847016438:AAFhpb7rz5-6AQ3f2iEvlafj3K_i25AAeIs"
        #        "5213943599:AAEfxy84Q5rY9WF5gsudOP4Zbec0YOPoua4"
        #TOKEN = "5607978232:AAHMWzK-nksRMtkcZv_3pCyGE7mfUXrZbYE"

GOOGLESHEETSKEY = "1LQpiv9JwT_64dKYAcOlvVobClnItOSYLut7_Ze8Kr_g"

PAYMENTPROVIDERTOKEN = "535936410:LIVE:5847016438_1a635d88-6ed9-4260-9538-2532dcea6d7e"

test_limit = 10

list_active_players = []

question_messages = []

levels_rank = {
    "Senior" : 3,
    "Middle" : 2,
    "Junior" : 1
}
rank_levels = {
    "3":"Senior",
    "2":"Middle",
    "1":"Junior"
}

pos = {
    '1' : '🥇',
    '2' : '🥈',
    '3' : '🥉'
}

welcome_pages = {
    "1" : ("Welcome.mp3", {"ХТО ЦЕ РОЗМОВЛЯЄ?":"2"}),
    "ХТО ЦЕ РОЗМОВЛЯЄ?" : ("who is talking.mp3", {"Що таке АНГЛіЗі ?":"3"}),
    "Що таке АНГЛіЗі ?" : ("What is ANGLISI _.mp3", {"Можна ще деталей?":"4"}),
    "Можна ще деталей?" : ("more details.mp3", {"Як проходить АНГЛіЗі?":"5"}),
    "Як проходить АНГЛіЗі?" : ("How to pass ANGLISI.mp3", {"Скільки це коштує?":"6"}),
    "Скільки це коштує?" : ("How much does it cost.mp3", {"ЗАРЕЄСТРУВАТИСЬ":"reg", "В Мене є ще питання":"7"}),
    "В Мене є ще питання" : (None, {"Як отримати PROMOTION?":"8","Детальніше про Рівні" : "9" ,"У МЕНЕ Є ВЛАСНЕ ЗАПИТАННЯ":"10", "Назад":"11"}),
    "Як отримати PROMOTION?" : ("How to get PROMOTION_.mp3", {}),
    "Детальніше про Рівні" : ("More about levels.mp3", {}),
    "У МЕНЕ Є ВЛАСНЕ ЗАПИТАННЯ" : ("I have my own question.mp3", {}),
    "Назад" : (None, {"ЗАРЕЄСТРУВАТИСЬ":"reg", "В Мене є ще питання":"7"})
}

bttns_list = ("ХТО ЦЕ РОЗМОВЛЯЄ?", "Що таке АНГЛіЗі ?", "Можна ще деталей?", "Скільки це коштує?", "Як проходить АНГЛіЗі?","ЗАРЕЄСТРУВАТИСЬ", "В Мене є ще питання", "Як отримати PROMOTION?",
                "Детальніше про Рівні", "У МЕНЕ Є ВЛАСНЕ ЗАПИТАННЯ", "Назад")