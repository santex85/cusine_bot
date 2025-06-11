# gunicorn.conf.py
# Импортируем функции on_startup и on_shutdown из вашего основного файла приложения
from app import on_startup, on_shutdown

# Привязываем функции к хукам Gunicorn
# Gunicorn будет вызывать эти функции при старте и остановке воркеров
# 'post_worker_init' - хороший хук для on_startup
# 'worker_exit' - хороший хук для on_shutdown
def post_worker_init(worker):
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup(None))

def worker_exit(server, worker):
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_shutdown(None))

# Другие возможные настройки, если понадобятся
# bind = "0.0.0.0:8080"
# workers = 1
