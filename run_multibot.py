# для переменных окружения
import os
from dotenv import load_dotenv
load_dotenv()

# здесь лучше перейти в файлы и почитать
from parts import max_part, vk_part
from classes.multibot import Multibot

async def run():
    # создание экземпляров ботов
    maxbot = max_part.MAX(os.getenv("MAXTOKEN"))
    vkbot = vk_part.VK(os.getenv("VKTOKEN"))

    # создание экземпляра
    multibot = Multibot()

    # передача управления ботами
    multibot.add_max(maxbot)
    multibot.add_vk(vkbot)

    # запуск
    await multibot.run_polling()