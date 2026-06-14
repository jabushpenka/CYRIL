import asyncio
import datetime
import json
from hashlib import sha256

import os
from dotenv import load_dotenv
load_dotenv()
SECRETKEY = os.getenv("SECRETKEY")

from classes.MyUpdate import MyUpdate
from classes.database import CyrilDB
from classes.connections import ConnectionManager
from parts.max_part import MAX
from parts.vk_part import VK

# мастер-класс, реализующий логику (универсальную для всех ботов)
class Multibot:
    def __init__(self):
        self.db : CyrilDB = CyrilDB()
        self.manager : ConnectionManager = ConnectionManager()
        self.maxBot : MAX = None
        self.vkBot : VK = None
        self.running : bool = False

    def set_database(self, db : CyrilDB):
        self.db = db

    def set_manager(self, manager : ConnectionManager):
        self.manager = manager

    # указатель на бот (MAX)
    def add_max(self, maxbot : MAX):
        self.maxBot = maxbot

    # указатель на бот (VK)
    def add_vk(self, vkbot : VK):
        self.vkBot = vkbot

    # запуск бота (MAX)
    async def run_max(self):
        while self.running:
            batch = await self.maxBot.poll()
            for upd in batch:
                await self.handle(upd)
        return

    # запуск бота (MAX)
    async def run_vk(self):
        while self.running:
            batch = await self.vkBot.poll()
            for upd in batch:
                await self.handle(upd)
        return

    # запуск сразу всех ботов (асинхронно)
    async def run_polling(self):
        if not self.running:
            task_max = asyncio.create_task(self.run_max())
            task_vk = asyncio.create_task(self.run_vk())

            self.running = True

            await task_max
            await task_vk

            self.running = False
            return
        else: return

    # отправка сообщения при помощи одного из ботов
    async def send_message(self, messenger_id, chat_id_in_messenger, text):
        if messenger_id == 3:
            await self.maxBot.send_message(chat_id_in_messenger,text)
        elif messenger_id == 2:
            await self.vkBot.send_message(chat_id_in_messenger,text)

    # обработчик всех входящих сообщений
    async def handle(self, upd : MyUpdate):
        messenger_id = upd.messenger_id
        chat_id_in_messenger = upd.chat_id_in_messenger
        if not self.db.chat_exists(messenger_id,chat_id_in_messenger):
            self.db.chat_add(messenger_id, chat_id_in_messenger)
            return

        if upd.text.startswith("/"):
            prefix = upd.text.split(' ')[0]
            await self.handle_command(prefix,upd)

        chat_id = self.db.chat_get_id(messenger_id, chat_id_in_messenger)
        message_id_in_chat = upd.message_id_in_chat
        text = upd.text
        fromuser = upd.fromuser

        self.db.message_add(chat_id, message_id_in_chat, text, fromuser)

        # рассылка сообщения по группе (на веб)
        if self.db.chat_has_group(chat_id):
            group_id = self.db.chat_get_group_id(chat_id)
            data = {"chat_id": chat_id, "text": text, "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            await self.manager.broadcast(group_id, json.dumps(data))
            return

    # обработчик команд, TODO: (слишком огромный, реализовать через декораторы)
    async def handle_command(self, cmd: str, upd : MyUpdate):
        messenger_id = upd.messenger_id
        chat_id_in_messenger = upd.chat_id_in_messenger
        text = upd.text
        fromuser = upd.fromuser

        chat_id = self.db.chat_get_id(messenger_id, chat_id_in_messenger)

        split = text.split()


        ### логика создания группы
        if cmd == "/group":
            if self.db.chat_has_group(chat_id):
                group_id = self.db.chat_get_group_id(chat_id)
                group_name = self.db.group_get_name(group_id)
                group_id = self.db.chat_get_group_id(chat_id)
                await self.send_message(messenger_id, chat_id_in_messenger,f"чат уже в группе {group_id} - {group_name}")
                return

            if len(split) != 3:
                await self.send_message(messenger_id,chat_id_in_messenger,"формат /group [название] [пароль]")
                return

            group_name = split[1]
            pword = split[2]
            group_pword = sha256(pword.encode()).hexdigest()
            group_id = self.db.group_add(group_name, group_pword)

            secret = SECRETKEY + str(group_id)
            group_hashkey = sha256(secret.encode()).hexdigest()
            self.db.group_set_hashkey(group_id, group_hashkey)

            self.db.chat_link(group_id, chat_id)
            await self.send_message(messenger_id, chat_id_in_messenger, f"готово, теперь в другом чате используйте\n"
                                                                        f"/link {group_id} {pword}\n"
                                                                        f"чтобы подключить его к группе \"{group_name}\"\n"
                                                                        f"читайте подключённые чаты через сайт, ваш ключ:\n"
                                                                        f"{group_hashkey}")


        ### логика подключения чата к группе
        elif cmd == "/link":
            if len(split) != 3:
                await self.send_message(messenger_id,chat_id_in_messenger,"формат /link [ID] [пароль]")
                return

            group_id = split[1]
            pword = split[2]
            hashkey = sha256(pword.encode()).hexdigest()

            if self.db.group_check_pword(group_id, hashkey):
                self.db.chat_link(group_id, chat_id)
                group_name = self.db.group_get_name(group_id)
                await self.send_message(messenger_id, chat_id_in_messenger,f"теперь вы в группе {group_name}")
            else:
                await self.send_message(messenger_id, chat_id_in_messenger, f"не верные данные")


        # логика отключения чата от группы
        elif cmd == "/unlink":
            if not self.db.chat_has_group(chat_id):
                await self.send_message(messenger_id, chat_id_in_messenger,f"чат не в группе")
                return
            self.db.chat_unlink(chat_id)
            await self.send_message(messenger_id, chat_id_in_messenger, f"теперь чат не в группе")


        # логика рассылки сообщений (НА ВСЕ МЕССЕНДЖЕРЫ!!! 🥳🥳🥳)
        elif cmd == "/share":
            if self.db.chat_has_group(chat_id):
                group_id = self.db.chat_get_group_id(chat_id)
                t = f"рассылка от {fromuser}:" + text.removeprefix("/share")
                await self.share(chat_id, group_id, t)
                return


    # обработчик рассылки сообщений
    async def share(self, init_chat_id : int | None, group_id, message):
        chats = self.db.group_get_chats(group_id)
        for chat in chats:
            chat_id = chat[0]
            messenger_id = chat[1]
            chat_id_in_messenger = chat[2]

            if chat_id == init_chat_id:
                continue

            if messenger_id == 3:
                await self.maxBot.send_message(chat_id_in_messenger, message)
            elif messenger_id == 2:
                await self.vkBot.send_message(chat_id_in_messenger, message)
        return