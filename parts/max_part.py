from maxapi import Bot, Dispatcher

from classes.MyUpdate import MyUpdate

# интерфейс позволяющий взаимодействовать с ботом (MAX) из мастер-класса
class MAX:
    dp = Dispatcher()
    messenger_id = 3
    def __init__(self, token : str):
        self.bot : Bot = Bot(token)

    # опрос серверов (MAX), возвращает список обновлений MyUpdate[]
    async def poll(self):
        result = list()
        try:
            updates = await self.bot.get_updates()

            for update in updates['updates']:
                if update['update_type'] == 'message_created':
                    chat_id_in_messenger = update['message']['recipient']['chat_id']
                    message_id_in_chat = update['message']['body']['seq']
                    text = update['message']['body']['text']
                    #print("max: ",chat_id,text)
                    result.append(MyUpdate(self.messenger_id, chat_id_in_messenger, message_id_in_chat, text))

            return result
        except Exception as e:
            print("ошибка:",e)
            return result

    # отправка сообщения в чат (МАХ)
    async def send_message(self, chat_id, text):
        await self.bot.send_message(chat_id=chat_id,text=text)