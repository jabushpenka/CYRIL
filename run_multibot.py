# для переменных окружения
import os
from dotenv import load_dotenv
load_dotenv()

# здесь лучше перейти в файлы и почитать
from parts import max_part, vk_part
from classes.multibot import Multibot
from api import manager, db

# создание экземпляра
multibot = Multibot()

async def run():
    if not multibot.running:
        # создание экземпляров ботов
        maxbot = max_part.MAX(os.getenv("MAXTOKEN"))
        vkbot = vk_part.VK(os.getenv("VKTOKEN"))

        # добавление менеджера подключений (для рассылок по websocket)
        multibot.set_manager(manager)

        # добавление базы данных (для синхронизации с API)
        multibot.set_database(db)

        # передача управления ботами
        multibot.add_max(maxbot)
        multibot.add_vk(vkbot)

        # запуск
        return await multibot.run_polling()
    else:
        return '-Мультибот, где ты был?\n-Бегал.'
