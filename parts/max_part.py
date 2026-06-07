from maxapi import Bot, Dispatcher

from classes.MyUpdate import MyUpdate

# интерфейс позволяющий взаимодействовать с ботом (MAX) из мастер-класса
class MAX:
    dp = Dispatcher()
    messenger_id = 3
    def __init__(self, token : str):
        self.bot = Bot(token)

    # опрос серверов (MAX), возвращает массив обновлений MyUpdate[]
    async def poll(self):
        result = list()
        try:
            updates = await self.bot.get_updates()

            for update in updates['updates']:
                chat_id = update['message']['recipient']['chat_id']
                message_id_in_chat = await self.count_messages(chat_id)
                text = update['message']['body']['text']
                #print("max: ",chat_id,text)
                result.append(MyUpdate(self.messenger_id, chat_id, message_id_in_chat, text))

            return result
        except Exception as e:
            print("ошибка:",e)
            return result

    # подсчёт количества сообщений в чате
    async def count_messages(self, chat_id):
        messages = await self.bot.get_messages(chat_id)
        return len(messages.messages)

    # отправка сообщения в чат (МАХ)
    async def send_message(self, chat_id, text):
        await self.bot.send_message(chat_id=chat_id,text=text)