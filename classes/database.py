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

        self.cur = self.conn.cursor()

    # ОПЕРАЦИИ ДЛЯ ЧАТОВ

    def chat_exists(self, messenger_id, chat_id_in_messenger):
        """Проверяем, есть ли чат в базе"""
        try:
            self.cur.execute("SELECT chat_id FROM chats WHERE messenger_id = %s AND chat_id_in_messenger = %s",
                             (messenger_id, chat_id_in_messenger))
            result = self.cur.fetchall()
            return bool(len(result))
        except Exception as e:
            return e

    def chat_get_id(self, messenger_id, chat_id_in_messenger):
        """Достаём ID чата из базы"""
        try:
            self.cur.execute("SELECT chat_id FROM chats WHERE messenger_id = %s AND chat_id_in_messenger = %s",
                             (messenger_id, chat_id_in_messenger))
            result = self.cur.fetchone()
            return result[0]
        except Exception as e:
            return e

    def chat_add(self, messenger_id, chat_id_in_messenger):
        """Добавляем чат в базу"""
        try:
            self.cur.execute("INSERT INTO chats (messenger_id,chat_id_in_messenger) VALUES (%s, %s) RETURNING chat_id;",
                            (messenger_id, chat_id_in_messenger))
            result = self.cur.fetchone()
            self.conn.commit()
            return result[0]
        except Exception as e:
            self.conn.rollback()
            return e

    def chat_has_group(self, chat_id):
        """Проверяем, есть ли у чата группа"""
        try:
            self.cur.execute("SELECT group_id FROM chats WHERE chat_id = %s AND group_id > -1",
                             (chat_id,))
            result = self.cur.fetchall()
            print()
            return bool(len(result))
        except Exception as e:
            return e

    def chat_get_group_id(self, chat_id):
        """Достаём ID группы, к которой привязан чат"""
        try:
            self.cur.execute("SELECT group_id FROM chats WHERE chat_id = %s",
                             (chat_id,))
            result = self.cur.fetchone()
            return result[0]
        except Exception as e:
            return e

    def chat_get_messages(self, chat_id, skip: int = 0, limit: int = 10):
        """Выбораем из произвольной таблицы"""
        try:
            self.cur.execute(f"SELECT * FROM messages WHERE chat_id = %s OFFSET %s LIMIT %s;",
                             (chat_id, skip, limit))
            result = self.cur.fetchall()
            return result
        except Exception as e:
            return e

    def chat_link(self, group_id, chat_id):
        """Присоединяем чат к группе"""
        try:
            self.cur.execute("UPDATE chats SET group_id = %s WHERE chat_id = %s",
                             (group_id, chat_id))
            return self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            return e

    def chat_unlink(self, chat_id):
        """Отсоединяем чат от группы"""
        try:
            self.cur.execute("UPDATE chats SET group_id = NULL WHERE chat_id = %s", (chat_id,))
            return self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            return e

    # ОПЕРАЦИИ ДЛЯ ГРУПП (groupps)

    def group_exists(self, group_id):
        """Проверяем, есть ли группа в базе"""
        try:
            self.cur.execute("SELECT group_id FROM groupps WHERE group_id = %s",
                                     (group_id,))
            result = self.cur.fetchall()
            return bool(len(result))
        except Exception as e:
            return e

    def group_get_name(self, group_id):
        """Получаем имя группы из базы"""
        try:
            self.cur.execute("SELECT group_name FROM groupps WHERE group_id = %s", (group_id,))
            result = self.cur.fetchone()
            return result[0]
        except Exception as e:
            return e

    def group_add(self, name, hashkey):
        """Создаем группу"""
        try:
            self.cur.execute("INSERT INTO groupps (group_name, hashkey) VALUES (%s,%s) RETURNING group_id",
                                      (name,hashkey))
            result = self.cur.fetchone()
            self.conn.commit()
            return result[0]
        except Exception as e:
            self.conn.rollback()
            return e

    def group_has_chats(self, group_id):
        """Проверяем есть ли у группы чаты"""
        try:
            self.cur.execute("SELECT chat_id FROM chats WHERE group_id = %s", (group_id,))
            result = self.cur.fetchall()
            return bool(len(result))
        except Exception as e:
            return e

    def group_get_chats(self, group_id):
        """Получаем список чатов из группы"""
        try:
            self.cur.execute("SELECT chat_id,messenger_id,chat_id_in_messenger FROM chats WHERE group_id = %s",(group_id,))
            result = self.cur.fetchall()
            return result
        except Exception as e:
            return e

    def group_remove(self, group_id):
        """Удаляем группу из базы"""
        try:
            self.cur.execute("DELETE FROM groupps WHERE group_id = %s", (group_id,))
            return self.conn.commit()
        except Exception as e:
            return e

    def group_check_hashkey(self, group_id, hashkey):
        """Проверяем ключ от группы"""
        try:
            self.cur.execute("SELECT group_id FROM groupps WHERE (group_ID,hashkey) = (%s,%s)",(group_id,hashkey))
            result = self.cur.fetchall()
            return bool(len(result))
        except Exception as e:
            return e

    # ОПЕРАЦИИ ДЛЯ СООБЩЕНИЙ (messages)
    def message_add(self, chat_id, message_id_in_chat, text):
        """Добавляем сообщение в базу"""
        try:
            self.cur.execute("INSERT INTO messages (chat_id,message_id_in_chat,text) VALUES (%s,%s,%s)",
                             (chat_id, message_id_in_chat, text))
            return self.conn.commit()
        except Exception as e:
            return e

    # UTILITIES
    def columns(self, table : str = 'groupps'):
        """Получение столбцов в таблице"""
        try:
            self.cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s",
                             (table,))
            tuples = self.cur.fetchall()
            result = [tup[0] for tup in tuples]
            return result
        except Exception as e:
            return e

    def select(self, table : str = 'groupps', skip: int = 0, limit: int = 10):
        """Выбораем из произвольной таблицы"""
        try:
            self.cur.execute(f"SELECT * FROM {table} OFFSET %s LIMIT %s;", (skip, limit))
            result = self.cur.fetchall()
            return result
        except Exception as e:
            return e

    def close(self):
        """Закрываем соединение с БД"""
        self.conn.close()