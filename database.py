import sqlite3

class CyrilDB:

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    # ОПЕРАЦИИ ДЛЯ ЧАТОВ (chats)

    def chat_exists(self, messenger_id, chat_id_in_messenger):
        """Проверяем, есть ли чат в базе"""
        result = self.cursor.execute("SELECT `ID` FROM `chats` WHERE `messenger_id` = ? AND `chat_id_in_messenger` = ?",
                                     (messenger_id, chat_id_in_messenger))
        return bool(len(result.fetchall()))

    def get_chat_id(self, messenger_id, chat_id_in_messenger):
        """Достаём ID чата в базе"""
        result = self.cursor.execute("SELECT `ID` FROM `chats` WHERE `messenger_id` = ? AND `chat_id_in_messenger` = ?",
                                     (messenger_id, chat_id_in_messenger))
        return result.fetchone()[0]

    def add_chat(self, messenger_id, chat_id_in_messenger):
        """Добавляем чат в базу"""
        self.cursor.execute("INSERT INTO `chats` (`messenger_id`,`chat_id_in_messenger`) VALUES (?,?)",
                            (messenger_id, chat_id_in_messenger,))
        return self.conn.commit()

    # ОПЕРАЦИИ ДЛЯ СВЯЗИ ЧАТОВ С ГРУППАМИ (chats -> groups)

    def chat_has_group(self, chat_id):
        """Проверяем, есть ли у чата группа"""
        result = self.cursor.execute("SELECT `group_id` FROM `chats` WHERE `ID` = ?",
                                     (chat_id,))
        if result.fetchone()[0]:
            return True
        else:
            return False

    def get_group_id(self, chat_id):
        """Достаём ID группы, к которой привязан чат"""
        result = self.cursor.execute("SELECT `group_id` FROM `chats` WHERE `ID` = ?",
                                     (chat_id,))
        return result.fetchone()[0]

    def link_chat(self, group_id, chat_id):
        """Присоединяем чат к группе"""
        self.cursor.execute("UPDATE `chats` SET `group_id` = ? WHERE `ID` = ?",
                            (group_id, chat_id))
        return self.conn.commit()

    def unlink_chat(self, chat_id):
        """Отсоединяем чат от группы"""
        self.cursor.execute("UPDATE `chats` SET `group_id` = NULL WHERE `ID` = ?", (chat_id,))
        return self.conn.commit()

    # ОПЕРАЦИИ ДЛЯ ГРУПП (groups)

    def group_exists(self, group_id):
        """Проверяем, есть ли группа в базе"""
        result = self.cursor.execute("SELECT `ID` FROM `groups` WHERE `ID` = ?",
                                     (group_id,))
        return bool(len(result.fetchall()))

    def get_group_name(self, group_id):
        """Получаем имя группы из базы"""
        result = self.cursor.execute("SELECT `name` FROM `groups` WHERE `ID` = ?", (group_id,))
        return result.fetchone()[0]

    def add_group(self, timezone, name, password):
        """Создаем группу"""
        result = self.cursor.execute("INSERT INTO `groups` (`timezone`,`name`,`password`) VALUES (?,?,?) RETURNING `ID`",
                                     (timezone, name,password)).fetchone()[0]
        self.conn.commit()
        return result

    def group_has_chats(self, group_id):
        """Проверяем есть ли у группы чаты"""
        result = self.cursor.execute("SELECT `ID` FROM `chats` WHERE `group_id` = ?", (group_id,))
        return bool(len(result.fetchall()))

    def group_chats(self,group_id): # стоит доработать
        """Получаем список чатов из группы"""
        result = self.cursor.execute("SELECT `ID`,`messenger_id`,`chat_id_in_messenger` FROM `chats` WHERE `group_id` = ?",(group_id,))
        return result.fetchall()

    def remove_group(self, group_id):
        """Удаляем группу из базы"""
        self.cursor.execute("DELETE FROM `groups` WHERE ID = ?", (group_id,))
        return self.conn.commit()

    def group_password(self,group_id,password):
        """Проверка пароля от группы"""
        result = self.cursor.execute("SELECT `ID` FROM `groups` WHERE (`ID`,`password`) = (?,?)",(group_id,password))
        return bool(len(result.fetchall()))

    # ОПЕРАЦИИ ДЛЯ СООБЩЕНИЙ (messages)

    def add_message(self, chat_id, message_id_in_chat, text):
        self.cursor.execute("INSERT INTO `messages` (`chat_id`,`message_id_in_chat`,`text`) VALUES (?,?,?)",
                            (chat_id, message_id_in_chat, text))
        return self.conn.commit()

    def close(self):
        """Закрываем соединение с БД"""
        self.conn.close()
