from aiogram.dispatcher.filters.state import StatesGroup
from aiogram.dispatcher.filters.state import State
from aiogram_dialog import DialogManager
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Jinja
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Row, Cancel, Button
from aiogram.types import ParseMode
from aiogram.types import CallbackQuery


class Show_fav_results_state(StatesGroup):
    show = State()


class Show_favorite_results_dialog():
    def __init__(self, database):
        self.db = database
        self.html_text = Jinja("""""")
        self.image = StaticMedia(url='None')
        self.states_group = Show_fav_results_state()
        self.dialog = self.get_dialog()

    def get_dialog(self):
        self.html_text = Jinja("""""")
        return Dialog(
            Window(
                self.html_text,
                self.image,
                Row(
                    Button(Const("Назад"), id="down", on_click=self.prev_add, ),
                    Button(Const("Вперёд"), id="up", on_click=self.next_add, ),
                ),
                Button(Const("Удалить из избранного"), id="delete_from_favorite", on_click=self.delete_from_favorite, ),
                Cancel(Const("Отмена"), on_click=self.clean_memory),
                parse_mode=ParseMode.HTML,
                state=self.states_group.show,
                getter=self.get_result_data_from_bd
            )
        )

    async def get_result_data_from_bd(self, **kwargs):
        async with kwargs['state'].proxy() as data:
            if 'result' not in data:
                data.update({'result': None})
            first_result = []
            if data.get('result') is None or data.get('result') == []:
                data['result'] = self.db.get_user_result(kwargs['state'].chat, 'fav')
                if data['result'] != []:
                    data['current_add'] = 0
                    data['next_add'] = 1
                    data['prev_add'] = 0
                    self.html_text.template_text = "<b>{{title}}</b>\n" \
                                                   "<b>ID : </b>{{appart[0]}}\n" \
                                                   "<b>Ссылка : </b><a href='{{appart[1]}}'>Полное объявление</a>\n" \
                                                   "<b>Площадь : </b>{{appart[3]}}\n" \
                                                   "<b>Количество комнат : </b>{{appart[4]}}\n" \
                                                   "<b>Цена : </b>{{appart[5]}}\n" \
                                                   "<b>Дата публикации : </b>{{appart[6]}}\n" \
                                                   "<b>Район: </b>{{appart[7]}}"
                    first_result = data['result'][0]
                    self.image.url.text = data['result'][0][2]
                else:
                    self.html_text.template_text = """<b>Ничего нет</b>"""
                    self.image.url.text = 'http://s1.iconbird.com/ico/0612/GooglePlusInterfaceIcons/w128h1281338911623emoticonsad.png'
                    return {
                        "appart": self.html_text.template_text
                    }

            return {
                "title": "Квартира:",
                "appart": first_result
            }

    def construct_dialog_str(self, app):
        return f"<b>Квартира</b>\n" \
               f"<b>ID :</b>{app[0]}\n" \
               f"<b>Ссылка :</b><a href='{app[1]}'>link</a>\n" \
               f"<b>Площадь :</b>{app[3]}\n" \
               f"<b>Количество комнат :</b>{app[4]}\n" \
               f"<b>Цена :</b>{app[5]}\n" \
               f"<b>Дата публикации :</b>{app[6]}\n" \
               f"<b>Район: </b>{app[7]}"

    # Смена содержания диалога на следующее объявление
    async def get_next_from_stor(self, manager):
        async with manager.data['state'].proxy() as data:
            if data['result'] != []:
                if data['current_add'] + 1 > len(data['result']) - 1:
                    next_app = data['result'][data['current_add']]
                else:
                    next_app = data['result'][data['current_add'] + 1]
                next_str = self.construct_dialog_str(next_app)
                img = next_app[2]
                if data['current_add'] != len(data['result']) - 1:
                    data['current_add'] += 1
                return next_str, img
            else:
                next_str = """<b>Ничего нет</b>"""
                img = 'http://s1.iconbird.com/ico/0612/GooglePlusInterfaceIcons/w128h1281338911623emoticonsad.png'
                return next_str, img

    # Смена содержания диалога на предыдущее объявление
    async def get_prev_from_stor(self, manager):
        async with manager.data['state'].proxy() as data:
            if data['result'] != []:
                if data['current_add'] - 1 < 0:
                    next_app = data['result'][data['current_add']]
                else:
                    next_app = data['result'][data['current_add'] - 1]
                next_str = self.construct_dialog_str(next_app)
                if data['current_add'] >= 1:
                    data['current_add'] -= 1
                img = next_app[2]
                return next_str, img
            else:
                next_str = """<b>Ничего нет</b>"""
                img = 'http://s1.iconbird.com/ico/0612/GooglePlusInterfaceIcons/w128h1281338911623emoticonsad.png'
                return next_str, img

    # Обработчик кнопки следующего объявления
    async def next_add(self, c: CallbackQuery, button: Button, manager: DialogManager):
        str, img = await self.get_next_from_stor(manager)
        self.image.url.text = img
        if str:
            self.html_text.template_text = (str)

    # Обработчик кнопки предыдущего объявления
    async def prev_add(self, c: CallbackQuery, button: Button, manager: DialogManager):
        str, img = await self.get_prev_from_stor(manager)
        self.image.url.text = img
        if str:
            self.html_text.template_text = (str)

    async def clean_memory(self, *args):
        async with args[2].data['state'].proxy() as data:
            if data.get('result'):
                data['result'] = None

    async def delete_from_favorite(self, c: CallbackQuery, button: Button, manager: DialogManager):
        idfav = await self.get_favorite_id(manager)
        if idfav is not None:
            async with manager.data['state'].proxy() as data:
                data['result'].pop([data['current_add']][0])
            await self.prev_add(c, button, manager)
            self.db.delete_from_favorite(manager.event.from_user.id, idfav)

    # Получить id текущего объявления
    async def get_favorite_id(self, manager):
        async with manager.data['state'].proxy() as data:
            if data['result'] != []:
                return data['result'][data['current_add']][0]
