import os
import sys
sys.path.append(os.path.abspath('celery_scheduler'))
sys.path.append(os.path.abspath('dbcontrolpack'))
sys.path.append(os.path.abspath('parser'))
sys.path.append(os.path.abspath('analyse_func'))

import logging
import time
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor
from aiogram_dialog import DialogRegistry, DialogManager, StartMode
from dbcontrolpack.db_control import Db_controller
from dialogs.set_find_params_dialog import Find_params_dialog
from dialogs.show_result_dialog import Show_results_dialog
from dialogs.show_favorite_result_dialog import Show_favorite_results_dialog
from dialogs.show_analyse_dialog import Show_analyse_dialog
from tasks_bot import start_find

logging.basicConfig(level=logging.INFO)
logging.getLogger("aiogram_dialog").setLevel(logging.DEBUG)
load_dotenv(override=True)


class MySahibindenBot():
    def __init__(self):
        self.bot = Bot(token=os.environ.get('TOKEN'))
        self.storage = MemoryStorage()
        self.dp = Dispatcher(self.bot, storage=self.storage)
        self.dp.register_message_handler(self.start, text="/start", state="*")
        self.dp.register_message_handler(self.set_find_params, text="Параметры поиска", state="*")
        self.dp.register_message_handler(self.show, text="Показать варианты", state="*")
        self.dp.register_message_handler(self.show_favorite, text="Показать избранное", state="*")
        self.dp.register_message_handler(self.find, text="Поиск", state="*")
        self.dp.register_message_handler(self.show_analyse_dialog, text="Анализ", state="*")
        self.database = Db_controller()
        self.database.create_table()
        self.registry = DialogRegistry(self.dp)
        self.find_params_dialog = Find_params_dialog(self.database)
        self.find_params_states = self.find_params_dialog.states_group
        self.show_results_dialog = Show_results_dialog(self.database)
        self.show_results_states = self.show_results_dialog.states_group
        self.show_fav_results_dialog = Show_favorite_results_dialog(self.database)
        self.show_fav_results_states = self.show_fav_results_dialog.states_group
        self.show_analyse_dialog = Show_analyse_dialog(self.database)
        self.show_analyse_states = self.show_analyse_dialog.states_group
        self.registry.register(self.find_params_dialog.dialog)
        self.registry.register(self.show_results_dialog.dialog)
        self.registry.register(self.show_fav_results_dialog.dialog)
        self.registry.register(self.show_analyse_dialog.dialog)

    def start_bot(self):
        executor.start_polling(self.dp, skip_updates=True)

    def get_menu_keyboard(self):
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton('Параметры поиска'))
        kb.add(KeyboardButton('Поиск'))
        kb.row(KeyboardButton('Показать варианты'), KeyboardButton('Показать избранное'))
        kb.add(KeyboardButton('Анализ'))
        return kb

    async def start(self, m: Message, dialog_manager: DialogManager):
        userinfo = (
            m.from_user.id,
            m.from_user.username,
            m.from_user.first_name,
            m.from_user.last_name,
            time.ctime()
        )
        self.database.send_user_info(userinfo)
        await  m.answer(f'Добрый день {m.from_user.username}!\n'
                        f'Я бот помощник в поиске квартир на sahibinden.\n'
                        f'Что я уже умею:\n'
                        f'1) Настроить ваш поиск. Настраивается до трех разных фильтров. Можно и больше, но они будут перезаписываться.\n'
                        f'2) Запустить поиск по всем вашим фильтрам. это может занять некоторое время.\n'
                        f'3) Показывать результаты поиска. Есть возможность добавлять в избранное и смотреть потом только избранное.\n'
                        f'Если в выдаче ничего нет, значит под ваши параметры не попало никаких объявлений. попробуйте создать новый фильтр.\n'
                        f'В данный момент я ещё не готов к полноценной работе, но я стремлюсь!\n'
                        f'В будущем будет прикручена аналитика по ценам на отдельные сегменты квартир в больших районах Анталии.\n'
                        f'Она уже собирается. надо только придумать в каком виде выводить информацию.',
                        reply_markup=self.get_menu_keyboard())

    async def set_find_params(self, m: Message, dialog_manager: DialogManager):
        await dialog_manager.start(self.find_params_states.district, mode=StartMode.RESET_STACK)

    async def show(self, m: Message, dialog_manager: DialogManager):
        await dialog_manager.start(self.show_results_states.show, mode=StartMode.RESET_STACK)

    async def show_favorite(self, m: Message, dialog_manager: DialogManager):
        await dialog_manager.start(self.show_fav_results_states.show, mode=StartMode.RESET_STACK)

    async def show_analyse_dialog(self, m: Message, dialog_manager: DialogManager):
        await dialog_manager.start(self.show_analyse_states.show, mode=StartMode.RESET_STACK)

    async def find(self, m: Message, dialog_manager: DialogManager):
        await m.answer('Поиск запущен')
        # вызываем поиск start_search
        id = m.from_user.id
        start_find.delay(id)
        print('stop')


if __name__ == '__main__':
    Bot = MySahibindenBot()
    Bot.start_bot()
