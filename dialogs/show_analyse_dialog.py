from aiogram.dispatcher.filters.state import StatesGroup
from aiogram.dispatcher.filters.state import State
from aiogram_dialog import DialogManager
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Jinja
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Row, Cancel, Button, Radio
from aiogram.types import ParseMode
from aiogram.types import CallbackQuery
from analyse_func.analyse import get_graph
from operator import itemgetter
import io
import os
import shutil
from PIL import Image


class Show_analyse_dialog_state(StatesGroup):
    show = State()


class Show_analyse_dialog:
    def __init__(self, database):
        self.db = database
        self.set_districts()
        self.html_text = Jinja("""""")
        self.image = StaticMedia(path=f'{os.getcwd()}/analyse/None.png')
        self.states_group = Show_analyse_dialog_state()
        self.dialog = self.get_dialog()
        self.analyse_base = {
            'muratpasha': {
                '1_m': 1,
                '1_': 2,
                '2_m': 3,
                '2_': 4,
                '3_m': 5,
                '3_': 6
            },
            'konyalty': {
                '1_m': 7,
                '1_': 8,
                '2_m': 9,
                '2_': 10,
                '3_m': 11,
                '3_': 12
            },
            'aksu': {
                '1_m': 13,
                '1_': 14,
                '2_m': 14,
                '2_': 16,
                '3_m': 17,
                '3_': 18
            },
            'kepez': {
                '1_m': 19,
                '1_': 20,
                '2_m': 21,
                '2_': 22,
                '3_m': 23,
                '3_': 24
            },
        }

    def get_dialog(self):
        return Dialog(
            Window(
                self.html_text,
                self.image,
                self.districts,
                Row(
                    Button(Const("1+м"), id="1_m", on_click=self.change_analyse_picture, ),
                    Button(Const("1+"), id="1_", on_click=self.change_analyse_picture, ),
                    Button(Const("2+м"), id="2_m", on_click=self.change_analyse_picture, ),
                    Button(Const("2+"), id="2_", on_click=self.change_analyse_picture, ),
                    Button(Const("3+м"), id="3_m", on_click=self.change_analyse_picture, ),
                    Button(Const("3+"), id="3_", on_click=self.change_analyse_picture, ),
                ),
                Cancel(Const("Отмена"), on_click=self.clean_memory),
                parse_mode=ParseMode.HTML,
                state=self.states_group.show,
                getter=self.refresh_dialog_message
            )
        )

    def set_districts(self):
        self.district = [
            ("Муратпаша", 'muratpasha'),
            ("Кепез", 'kepez'),
            ("Коньялты", 'konyalty'),
            ("Аксу", 'aksu'),
        ]
        self.districts = Radio(
            Format("🔘 {item[0]}"),
            Format("◯ {item[0]}"),
            id="s_dates",
            item_id_getter=itemgetter(1),
            items=self.district,
        )

    async def prev_add(self, c: CallbackQuery, button: Button, manager: DialogManager):
        # print(os.getcwd())
        # os.makedirs(f"{os.getcwd()}/{kwargs['state']")
        return True

    async def change_analyse_picture(self, c: CallbackQuery, button: Button, manager: DialogManager):
        if self.districts.get_checked(manager):
            await self.set_analyse_id_in_state(manager, self.analyse_base[self.districts.get_checked(manager)][button.widget_id])
        else:
            await self.set_analyse_id_in_state(manager, self.analyse_base['muratpasha'][button.widget_id])
        return True

    async def set_analyse_id_in_state(self, manager: DialogManager, id):
        if self.districts.get_checked(manager):
            print(self.districts.get_checked(manager))
        async with manager.data['state'].proxy() as data:
            if 'id' in data:
                data['id'] = id
        return True

    async def clean_memory(self, c: CallbackQuery, button: Button, manager: DialogManager):
        pass

    async def clean_path(self, path):
        if os.path.exists(path):
            shutil.rmtree(path)

    async def refresh_pictute(self, id_url, id_user, path):
        await self.clean_path(path)
        os.makedirs(path, exist_ok=True)
        img = get_graph(id_url, self.db)
        img.savefig(f'{path}/{id_user}_{id_url}.png', format='png')

    async def refresh_dialog_message(self, **kwargs):
        path = f'{os.getcwd()}/analyse/{kwargs["state"].chat}'
        async with kwargs['state'].proxy() as data:
            if 'id' not in data or data['id'] == None:
                data.update({'id': 1})
                id_url = data['id']
                await self.refresh_pictute(1, kwargs["state"].chat, path)
            else:
                id_url = data['id']
                await self.refresh_pictute(data['id'], kwargs["state"].chat, path)
        self.image.path.text = f'{path}/{kwargs["state"].chat}_{id_url}.png'
        self.html_text.template_text = '<b>{{title}}</b>'
        return {"title": "test test test"}
