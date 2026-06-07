import asyncio
from hashlib import sha256

from classes.MyUpdate import MyUpdate
from classes.database import CyrilDB
from parts import max_part, vk_part


# мастер-класс, реализующий логику (универсальную для всех ботов)
class Multibot:
    def __init__(self):
        self.db = CyrilDB()
        self.maxBot = None
        self.vkBot = None

    # указатель на бот (MAX)
    def add_max(self, maxbot : max_part.MAX):
        self.maxBot = maxbot

    # указатель на бот (VK)
    def add_vk(self, vkbot : vk_part.VK):
        self.vkBot = vkbot

    # запуск бота (MAX)
    async def run_max(self):
        while True:
            batch = await self.maxBot.poll()
            for upd in batch:
                await self.handle(upd)

    # запуск бота (MAX)
    async def run_vk(self):
        while True:
            batch = await self.vkBot.poll()
            for upd in batch:
                await self.handle(upd)

    # запуск сразу всех ботов (асинхронно)
    async def run_polling(self):
        task_max = asyncio.create_task(self.run_max())
        task_vk = asyncio.create_task(self.run_vk())

        await task_max
        await task_vk

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
            return

        chat_id = self.db.chat_get_id(messenger_id, chat_id_in_messenger)
        message_id_in_chat = upd.message_id_in_chat
        return self.db.message_add(chat_id, message_id_in_chat, upd.text)

    # обработчик команд, (огромный, поэтому TODO: реализовать через декораторы или вынести)
    async def handle_command(self, cmd: str, upd : MyUpdate):
        messenger_id = upd.messenger_id
        chat_id_in_messenger = upd.chat_id_in_messenger
        text = upd.text

        chat_id = self.db.chat_get_id(messenger_id, chat_id_in_messenger)

        split = text.split()

        # логика создания группы
        if cmd == "/group":
            if self.db.chat_has_group(chat_id) == True:
                group_id = self.db.chat_get_group_id(chat_id)
                group_name = self.db.group_get_name(group_id)
                await self.send_message(messenger_id,chat_id_in_messenger,f"чат уже в группе {group_name}")
                return

            if len(split) != 3:
                await self.send_message(messenger_id,chat_id_in_messenger,"формат /group [название] [пароль]")
                return

            group_name = split[1]
            pword = split[2]
            group_hashkey = sha256(pword.encode()).hexdigest()
            group_id = self.db.group_add(group_name, group_hashkey)
            self.db.chat_link(group_id, chat_id)
            await self.send_message(messenger_id, chat_id_in_messenger, f"готово, теперь в другом чате используйте\n"
                                                                        f"/link {group_id} {pword}\n"
                                                                        f"чтобы подключить его к группе \"{group_name}\"")
        # логика подключения чата к группе
        elif cmd == "/link":
            if len(split) != 3:
                await self.send_message(messenger_id,chat_id_in_messenger,"формат /link [ID] [пароль]")
                return

            group_id = split[1]
            pword = split[2]
            hashkey = sha256(pword.encode()).hexdigest()

            if self.db.group_check_hashkey(group_id,hashkey) == True:
                self.db.chat_link(group_id, chat_id)
                group_name = self.db.group_get_name(group_id)
                await self.send_message(messenger_id, chat_id_in_messenger,f"теперь вы в группе {group_name}")
            else:
                await self.send_message(messenger_id, chat_id_in_messenger, f"не верные данные")
        # логика отключения чата от группы
        elif cmd == "/unlink":
            self.db.chat_unlink(chat_id)
            await self.send_message(messenger_id, chat_id_in_messenger, f"теперь вы не в группе")
        # логика рассылки сообщений (НА ВСЕ МЕССЕНДЖЕРЫ!!! 🥳🥳🥳)
        elif cmd == "/share":
            if self.db.chat_has_group(chat_id) == True:
                group_id = self.db.chat_get_group_id(chat_id)
                t = text.removeprefix("/share")
                await self.share(chat_id, group_id, t)
                return

    # обработчик рассылки сообщений
    async def share(self, init_chat_id, group_id, message):
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