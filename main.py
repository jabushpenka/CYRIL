# запуск мультибота
import asyncio
import run_multibot

# запуск API должен осуществляться в терминале командой:
# uvicorn api:app

if __name__ == '__main__':
    print('starting bot')
    asyncio.run(run_multibot.run())