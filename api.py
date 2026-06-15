from classes.database import CyrilDB
from classes.connections import ConnectionManager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# сам апи
app = FastAPI()

# подключения
app.add_middleware(
    CORSMiddleware,
    allow_origins=[  # потом поменять на домен
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://92.63.102.203:5174",
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

# Получить чаты (для дебага)
@app.get("/chats")
def get_chats(skip: int = 0, limit: int = 10):
    table = "chats"
    return pack(db.columns(table), db.select(table, skip, limit))

# Получить группы (для дебага)
@app.get("/groups")
def get_groups(skip: int = 0, limit: int = 10):
    table = "groupps"
    return pack(db.columns(table), db.select(table, skip, limit))

# Получить сообщения (для дебага)
@app.get("/messages")
def get_messages(skip: int = 0, limit: int = 10):
    table = "messages"
    return pack(db.columns(table), db.select(table, skip, limit))

# Получить платформ (для дебага)
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
@app.get("/chat_get_id", summary="получение ID чата")
def chat_get_id(messenger_id : int, chat_id_in_messenger : int):
    return db.chat_get_id(messenger_id, chat_id_in_messenger)

# добавление нового чата в базу
@app.post("/chat_add", summary="добавление нового чата в базу", include_in_schema=False)
def chat_add(messenger_id : int, chat_id_in_messenger : int):
    return db.chat_add(messenger_id, chat_id_in_messenger)

# проверка состоит ли чат в группе
@app.get("/chat_has_group", summary="проверка состоит ли чат в группе")
def chat_has_group(chat_id : int):
    return db.chat_has_group(chat_id)

# получение id группы, в которой состоит чат
@app.get("/chat_get_group_id", summary="получение ID группы чата")
def chat_get_group_id(chat_id : int):
    return db.chat_get_group_id(chat_id)
# получение сообщений из чата
@app.get("/chat_get_messages", summary="получение сообщений из чата")
def chat_get_messages(chat_id, skip: int = 0, limit: int = 50):
    keys = ['message_id_in_chat','text','date','fromuser'] # какая информация будет о каждом сообщении
    res = db.chat_get_messages(chat_id, skip, limit)
    for index, value in enumerate(res):
        res[index] = dict(zip(keys, value))
    return res

# присоединение чата к группе
@app.put("/chat_link", summary="присоединение чата к группе", include_in_schema=False)
def chat_link(group_id : int, chat_id : int):
    return db.chat_link(group_id, chat_id)

# отсоединение чата от группы
@app.put("/chat_unlink", summary="отсоединение чата от группы", include_in_schema=False)
def chat_unlink(chat_id : int):
    return db.chat_unlink(chat_id)


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
@app.post("/group_add", summary="добавление группы", include_in_schema=False)
def group_add(name : str, hashkey : str):
    return db.group_add(name, hashkey)

# смена ключа группы
@app.put("/group_set_hashkey", summary="отсоединение чата от группы", include_in_schema=False)
def group_set_hashkey(group_id : int, hashkey : str):
    return db.group_set_hashkey(group_id, hashkey)

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
@app.delete("/group_remove", summary="удаление группы", include_in_schema=False)
def group_remove(group_id : int):
    return db.group_remove(group_id)

# проверка ключа к группе
@app.get("/group_check_pword", summary="проверка пароля к группе")
def group_check_pword(group_id : int, pword : str):
    return db.group_check_pword(group_id, pword)

# получение группы по ключу
@app.get("/group_get_by_hashkey", summary="получение ID группы по ключу")
def group_get_by_hashkey(hashkey : str):
    return db.group_get_by_hashkey(hashkey)


# МЕНЕДЖЕР ВЕБСОКЕТОВ
manager = ConnectionManager()

# подключение websocket, рассылает сообщения всем подключениям из группы
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data : dict = await websocket.receive_json()

            try:
                int(data.get('group_id'))
            except ValueError as e:
                print(e)
                continue

            action = data.get('action')
            group_id = int(data.get('group_id'))

            if action == "add":
                manager.add_group(websocket, group_id)
                continue
            elif action == "remove":
                manager.remove_group(websocket, group_id)
                continue
            else: continue
    except WebSocketDisconnect:
        manager.disconnect(websocket)

############ НЕ трогать

# HTML для проверки websocket (см htmltest.py)
import htmltest
from fastapi.responses import HTMLResponse
@app.get("/test", include_in_schema=False)
async def get():
    return HTMLResponse(htmltest.html)

# запуск ботов через запрос в корень
from run_multibot import run
@app.get('/', include_in_schema=False)
async def root():
    return await run()