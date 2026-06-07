from classes.database import CyrilDB

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# сам апи
app = FastAPI()

# подключения
app.add_middleware(
    CORSMiddleware,
    allow_origins=[  # потом поменять на домен
        "http://localhost:5173",
        "http://127.18.0.1:5173",
        "http://130.49.148.168:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # POST, GET, PUT и т.д.
    allow_headers=["*"],
)

# бд
db = CyrilDB()

# Преобразование кортежей с бд в словарь (см следующую же функцию)
def pack(keys, list_of_tuples):
    for index, value in enumerate(list_of_tuples):
        list_of_tuples[index] = dict(zip(keys, value))
    return list_of_tuples

# Получить пользователей (для дебага)
@app.get("/chats")
def get_chats(skip: int = 0, limit: int = 10):
    table = "chats"
    return pack(db.columns(table), db.select(table, skip, limit))

# Получить группы (для дебага)
@app.get("/groups")
def get_groups(skip: int = 0, limit: int = 10):
    table = "groupps"
    return pack(db.columns(table), db.select(table, skip, limit))

# Получить группы (для дебага)
@app.get("/messages")
def get_messages(skip: int = 0, limit: int = 10):
    table = "messages"
    return pack(db.columns(table), db.select(table, skip, limit))

# Получить группы (для дебага)
@app.get("/platforms")
def get_platforms(skip: int = 0, limit: int = 10):
    table = "platforms"
    return pack(db.columns(table), db.select(table, skip, limit))

# ОПЕРАЦИИ ДЛЯ ЧАТОВ
# Проверка существования чата
@app.get("/chat_exists", summary="проверка существования чата")
def chat_exists(messenger_id : int, chat_id_in_messenger : int):
    return db.chat_exists(messenger_id, chat_id_in_messenger)

# получение id чата
@app.get("/chat_get_id", summary="получение id чата")
def chat_get_id(messenger_id : int, chat_id_in_messenger : int):
    return db.chat_get_id(messenger_id, chat_id_in_messenger)

# добавление нового чата в базу
@app.post("/chat_add", summary="НЕ делай это")
def chat_add(messenger_id : int, chat_id_in_messenger : int):
    return db.chat_add(messenger_id, chat_id_in_messenger)

# проверка состоит ли чат в группе
@app.get("/chat_has_group", summary="проверка состоит ли чат в группе")
def chat_has_group(chat_id : int):
    return db.chat_has_group(chat_id)

# получение id группы, в которой состоит чат
@app.get("/chat_get_group_id", summary="получение id группы чата")
def chat_get_group_id(chat_id : int):
    return db.chat_get_group_id(chat_id)

# присоединение чата к группе
@app.put("/chat_link", summary="НЕ делай это")
def chat_link(group_id : int, chat_id : int):
    return db.chat_link(group_id, chat_id)

# отсоединение чата от группы
@app.put("/chat_unlink", summary="НЕ делай это")
def chat_unlink(chat_id : int):
    return db.chat_unlink(chat_id)

def chat_get_messages(chat_id, skip: int = 0, limit: int = 10):
    table = "messages"
    return pack(table, db.chat_get_messages(chat_id, skip, limit))

# ОПЕРАЦИИ ДЛЯ ГРУПП
# проверка существования группы
@app.get("/group_exists", summary="проверка существования группы")
def group_exists(group_id : int):
    return db.group_exists(group_id)

# получение названия группы
@app.get("/group_get_name", summary="получение названия группы")
def group_get_name(group_id : int):
    return db.group_get_name(group_id)

# добавление группы
@app.post("/group_add", summary="НЕ делай это")
def group_add(name : str, hashkey : str):
    return db.group_add(name, hashkey)

# проверка есть ли в группе чаты
@app.get("/group_has_chats", summary="проверка есть ли в группе чаты")
def group_has_chats(group_id : int):
    return db.group_has_chats(group_id)

# получение чатов из группы
@app.get("/group_get_chats", summary="получение чатов из группы")
def group_get_chats(group_id : int):
    table = "chats"
    return pack(db.columns(table), db.group_get_chats(group_id))

# удаление группы
@app.delete("/group_remove", summary="НЕ делай это")
def group_remove(group_id : int):
    return db.group_remove(group_id)

# проверка ключа к группе
@app.get("/group_check_hashkey", summary="проверка ключа к группе")
def group_check_hashkey(group_id : int, hashkey : str):
    return db.group_check_hashkey(group_id,hashkey)

# ОПЕРАЦИИ ДЛЯ СООБЩЕНИЙ
# добавление сообщения в базу
@app.post("/message_add", description="не надо", summary="этого не будет НИКОГДА *раскаты грома*")
def message_add(chat_id : int, message_id_in_chat : int, text : str):
    return db.message_add(chat_id, message_id_in_chat, text)