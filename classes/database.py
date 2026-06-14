# переменные окружения
import os
from dotenv import load_dotenv

load_dotenv()

import psycopg2


# noinspection SpellCheckingInspection
class CyrilDB:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DBNAME"),
            user=os.getenv("DBUSER"),
            password=os.getenv("DBPWORD"),
            host=os.getenv("DBHOST")
        )

    # ОПЕРАЦИИ ДЛЯ ЧАТОВ

    def chat_exists(self, messenger_id: int, chat_id_in_messenger: int) -> bool:
        """Проверяем, есть ли чат в базе"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT chat_id FROM chats WHERE messenger_id = %s AND chat_id_in_messenger = %s",
                            (messenger_id, chat_id_in_messenger))
                result = cur.fetchall()
                return bool(len(result))
            except Exception as e:
                print(e)
                return False

    def chat_get_id(self, messenger_id: int, chat_id_in_messenger: int) -> int:
        """Достаём ID чата из базы"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT chat_id FROM chats WHERE messenger_id = %s AND chat_id_in_messenger = %s",
                            (messenger_id, chat_id_in_messenger))
                result = cur.fetchone()
                return result[0]
            except Exception as e:
                print(e)
                return -1

    def chat_add(self, messenger_id: int, chat_id_in_messenger: int) -> int:
        """Добавляем чат в базу"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO chats (messenger_id,chat_id_in_messenger) VALUES (%s, %s) RETURNING chat_id;",
                            (messenger_id, chat_id_in_messenger))
                result = cur.fetchone()
                self.conn.commit()
                return result[0]
            except Exception as e:
                print(e)
                self.conn.rollback()
                return -1

    def chat_has_group(self, chat_id: int) -> bool:
        """Проверяем, есть ли у чата группа"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT group_id FROM chats WHERE chat_id = %s AND group_id > -1",
                            (chat_id,))
                result = cur.fetchall()
                return bool(len(result))
            except Exception as e:
                print(e)
                return False

    def chat_get_group_id(self, chat_id: int) -> int:
        """Достаём ID группы, к которой привязан чат"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT group_id FROM chats WHERE chat_id = %s",
                            (chat_id,))
                result = cur.fetchone()
                return result[0]
            except Exception as e:
                print(e)
                return -1

    def chat_get_messages(self, chat_id: int, skip: int = 0, limit: int = 10) -> list:
        """Получаем из чата сообщения"""
        with self.conn.cursor() as cur:
            try:
                cur.execute(f"SELECT message_id_in_chat,text,date,fromuser FROM messages WHERE chat_id = %s"
                            f" ORDER BY date DESC OFFSET %s LIMIT %s;",
                            (chat_id, skip, limit))
                result = cur.fetchall()
                return result
            except Exception as e:
                print(e)
                return list()

    def chat_link(self, group_id: int, chat_id: int) -> bool:
        """Присоединяем чат к группе"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("UPDATE chats SET group_id = %s WHERE chat_id = %s",
                            (group_id, chat_id))
                self.conn.commit()
                return True
            except Exception as e:
                print(e)
                self.conn.rollback()
                return False

    def chat_unlink(self, chat_id: int) -> bool:
        """Отсоединяем чат от группы"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("UPDATE chats SET group_id = NULL WHERE chat_id = %s", (chat_id,))
                self.conn.commit()
                return True
            except Exception as e:
                print(e)
                self.conn.rollback()
                return False

    # ОПЕРАЦИИ ДЛЯ ГРУПП (groupps)

    def group_exists(self, group_id: int) -> bool:
        """Проверяем, есть ли группа в базе"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT group_id FROM groupps WHERE group_id = %s",
                            (group_id,))
                result = cur.fetchall()
                return bool(len(result))
            except Exception as e:
                print(e)
                return False

    def group_get_name(self, group_id: int) -> str:
        """Получаем имя группы из базы"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT group_name FROM groupps WHERE group_id = %s", (group_id,))
                result = cur.fetchone()
                return result[0]
            except Exception as e:
                print(e)
                return str()

    def group_add(self, name: int, pword: str) -> int:
        """Создаем группу"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO groupps (group_name, pword) VALUES (%s,%s) RETURNING group_id",
                            (name, pword))
                result = cur.fetchone()
                self.conn.commit()
                return result[0]
            except Exception as e:
                print(e)
                self.conn.rollback()
                return -1

    def group_set_hashkey(self, group_id: int, hashkey: str) -> bool:
        """Присоединяем чат к группе"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("UPDATE groupps SET hashkey = %s WHERE group_id = %s",
                            (hashkey, group_id))
                self.conn.commit()
                return True
            except Exception as e:
                print(e)
                self.conn.rollback()
                return False

    def group_has_chats(self, group_id: int) -> bool:
        """Проверяем есть ли у группы чаты"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT chat_id FROM chats WHERE group_id = %s", (group_id,))
                result = cur.fetchall()
                return bool(len(result))
            except Exception as e:
                print(e)
                return False

    def group_get_chats(self, group_id: int) -> list:
        """Получаем список чатов из группы"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT chat_id,messenger_id,chat_id_in_messenger FROM chats WHERE group_id = %s",
                            (group_id,))
                result = cur.fetchall()
                return result
            except Exception as e:
                print(e)
                return list()

    def group_remove(self, group_id: int) -> bool:
        """Удаляем группу из базы"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("DELETE FROM groupps WHERE group_id = %s", (group_id,))
                self.conn.commit()
                return True
            except Exception as e:
                print(e)
                self.conn.rollback()
                return False

    def group_check_pword(self, group_id: int, pword: str) -> bool:
        """Проверяем ключ от группы"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT group_id FROM groupps WHERE (group_ID,pword) = (%s,%s)", (group_id, pword))
                result = cur.fetchall()
                return bool(len(result))
            except Exception as e:
                print(e)
                return False

    def group_get_by_hashkey(self, hashkey: str) -> int:
        """Получаем группу по ключу"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT group_id FROM groupps WHERE hashkey = %s", (hashkey,))
                result = cur.fetchone()
                return result[0]
            except Exception as e:
                print(e)
                return -1

    # ОПЕРАЦИИ ДЛЯ СООБЩЕНИЙ (messages)
    def message_add(self, chat_id: int, message_id_in_chat: int, text: str, fromuser: str) -> bool:
        """Добавляем сообщение в базу"""
        with self.conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO messages (chat_id,message_id_in_chat,text,fromuser) VALUES (%s,%s,%s,%s)",
                            (chat_id, message_id_in_chat, text,fromuser))
                self.conn.commit()
                return True
            except Exception as e:
                print(e)
                self.conn.rollback()
                return False

    # UTILITIES
    def columns(self, table: str = 'groupps') -> list:
        """Получение столбцов в таблице"""
        with self.conn.cursor() as cur:
            try:
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s",
                            (table,))
                tuples = cur.fetchall()
                result = [tup[0] for tup in tuples]
                return result
            except Exception as e:
                print(e)
                return list()

    def select(self, table: str = 'groupps', skip: int = 0, limit: int = 10) -> list:
        """Выбораем из произвольной таблицы"""
        with self.conn.cursor() as cur:
            try:
                cur.execute(f"SELECT * FROM {table} OFFSET %s LIMIT %s;", (skip, limit))
                result = cur.fetchall()
                return result
            except Exception as e:
                print(e)
                return list()

    def close(self):
        """Закрываем соединение с БД"""
        self.conn.close()
