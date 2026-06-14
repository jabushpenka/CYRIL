from vkbottle.bot import Bot

from classes.MyUpdate import MyUpdate

# интерфейс позволяющий взаимодействовать с ботом (VK) из мастер-класса
class VK:
    bot = Bot()
    messenger_id = 2
    def __init__(self, token : str):
        self.bot = Bot(token)

    # опрос серверов (VK), возвращает массив обновлений MyUpdate[]
    async def poll(self):
        result = list()

        async for event in self.bot.polling.listen():
            updates = event.get("updates")
            if not updates:
                continue
            for update in updates:
                if update['type'] == 'message_new':
                    chat_id_in_messenger = update['object']['message']['peer_id']
                    message_id_in_chat = update['object']['message']['conversation_message_id']
                    text = update['object']['message']['text']

                    users_info = await self.bot.api.users.get(user_ids=update['object']['message']['from_id'])
                    fromuser = users_info[0].first_name
                    #print("vk: ",chat_id,text)
                    result.append(MyUpdate(self.messenger_id, chat_id_in_messenger, message_id_in_chat, text, fromuser))

            return result

    # отправка сообщения в чат (МАХ)
    async def send_message(self, chat_id, text):
        await self.bot.api.messages.send(peer_id=chat_id, message=text, random_id=0)