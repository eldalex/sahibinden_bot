import os
import sys

sys.path.append(os.path.abspath('celery_scheduler'))
sys.path.append(os.path.abspath('dbcontrolpack'))
sys.path.append(os.path.abspath('parser'))
sys.path.append(os.path.abspath('analyse_func'))

import logging
import time
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery, BotCommand
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
        self.bot.set_my_commands(self.set_bot_commands())
        self.dp.register_message_handler(self.start, text="/start", state="*")
        self.dp.register_message_handler(self.new_find_params, text="/set_find_params", state="*")
        self.dp.register_message_handler(self.show, text="/show_all", state="*")
        self.dp.register_message_handler(self.show_favorite, text="/show_favorite", state="*")
        self.dp.register_message_handler(self.find, text="/find", state="*")
        self.dp.register_message_handler(self.show_analyse_dialog, text="/analysis", state="*")
        self.dp.register_callback_query_handler(self.button_edit_filter,
                                                lambda c: c.data.split('|')[0] == 'edit_filter')
        self.dp.register_callback_query_handler(self.button_remove_filter,
                                                lambda c: c.data.split('|')[0] == 'remove_filter')
        self.dp.register_callback_query_handler(self.create_new_filter,
                                                lambda c: c.data == 'create_new_filter')
        self.dp.register_callback_query_handler(self.close_filters_redactor,
                                                lambda c: c.data == 'close_filters_redactor')
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

    def set_bot_commands(self):
        commands = [
            BotCommand(command='/start', description='Начать работу')
        ]
        return commands

    def start_bot(self):
        executor.start_polling(self.dp, skip_updates=True)

    async def start(self, m: Message, dialog_manager: DialogManager):
        userinfo = (
            m.from_user.id,
            m.from_user.username,
            m.from_user.first_name,
            m.from_user.last_name,
            time.ctime()
        )
        await self.bot.send_message(os.environ.get('MYID'),
                                    f'Новый пользователь!\nИмя: {userinfo[2]}\nФамилия: {userinfo[3]}\nЛогин: @{userinfo[1]}')
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
                        )

    async def show(self, m: Message, dialog_manager: DialogManager):
        await m.answer('варианты:')
        await dialog_manager.start(self.show_results_states.show, mode=StartMode.RESET_STACK)

    async def show_favorite(self, m: Message, dialog_manager: DialogManager):
        await m.answer('избранное:')
        await dialog_manager.start(self.show_fav_results_states.show, mode=StartMode.RESET_STACK)

    async def show_analyse_dialog(self, m: Message, dialog_manager: DialogManager):
        await dialog_manager.start(self.show_analyse_states.show, mode=StartMode.RESET_STACK, )

    async def create_new_filter(self, m: Message, dialog_manager: DialogManager):
        await dialog_manager.start(self.find_params_states.district, mode=StartMode.RESET_STACK)

    async def button_remove_filter(self, query: CallbackQuery, dialog_manager: DialogManager, **kwargs):
        id = int(query.data.split('|')[1].split('=')[1])
        self.database.remove_user_find_url(id)
        await self.bot.answer_callback_query(query.id)
        await query.message.delete()
        markup = await self.get_find_params_markup(query.from_user.id)
        await self.bot.send_message(query.from_user.id, 'Редактор фильтров!', reply_markup=markup)

    async def button_edit_filter(self, query: CallbackQuery, dialog_manager: DialogManager, **kwargs):
        id = int(query.data.split('|')[1].split('=')[1])
        url = self.database.get_one_user_find_url(id)
        params = url[0][1].split('?')[1].split('&')[1:-1]
        await self.bot.answer_callback_query(query.id)
        await dialog_manager.start(self.find_params_states.district, mode=StartMode.RESET_STACK,
                                   data={'params': params,
                                         'load': True,
                                         'save_id': id})

    async def get_description_from_url(self, url):
        towns = {'83': 'Муратпаша', '84': 'Кепез', '85': 'Коньялты', '86': 'Аксу'}
        rooms = {'38473': '1+1',
                 '1206094': '1.5+1',
                 '1213206': '2+0',
                 '38470': '2+1',
                 '1259450': '3+0'}
        params = url.split('?')[1].split('&')[:-1]
        params_dict = []
        for param in params:
            params_dict.append({param.split('=')[0]: param.split('=')[1]})
        description = ''
        for param in params_dict:
            if 'address_town' in param:
                description += towns[param['address_town']] + ' /'
        description = description[:-1]
        for param in params_dict:
            if 'a20' in param:
                description += ' | ' + rooms[param['a20']]
            elif 'price_max' in param:
                description += f'. До {param["price_max"]} TL'
        return description

    async def get_find_params_markup(self, user_id):
        urls = self.database.get_user_urls(user_id)
        markup = InlineKeyboardMarkup()
        new_filter_button = InlineKeyboardButton(text='Создать новый фильтр', callback_data=f'create_new_filter')
        markup.add(new_filter_button)
        for url in urls:
            button = InlineKeyboardButton(text=await self.get_description_from_url(url[1]),
                                          callback_data='none')
            button1 = InlineKeyboardButton(text=f"удалить", callback_data=f'remove_filter|id={url[0]}')
            button2 = InlineKeyboardButton(text=f"редактировать", callback_data=f'edit_filter|id={url[0]}')
            markup.row(button)
            markup.row(button1, button2)
        markup.add(InlineKeyboardButton(text='Отмена', callback_data=f'close_filters_redactor'))
        return markup

    async def close_filters_redactor(self, query: CallbackQuery, dialog_manager: DialogManager, **kwargs):
        await query.message.delete()

    async def new_find_params(self, m: Message, dialog_manager: DialogManager):
        markup = await self.get_find_params_markup(m.from_user.id)
        await self.bot.send_message(m.chat.id, 'Редактор фильтров!', reply_markup=markup)

    async def test_function(self, m: Message, dialog_manager: DialogManager, **kwargs):
        pass

    async def find(self, m: Message, dialog_manager: DialogManager):
        await m.answer('Поиск запущен')
        # вызываем поиск start_search
        id = m.from_user.id
        start_find.delay(id)


if __name__ == '__main__':
    Bot = MySahibindenBot()
    Bot.start_bot()
