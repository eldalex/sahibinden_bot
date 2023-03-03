import operator
from operator import itemgetter
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Row, Button, Multiselect, Radio, Back, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram.types import CallbackQuery
from aiogram.dispatcher.filters.state import StatesGroup, State


class Find_params_states(StatesGroup):
    district = State()
    room = State()
    year = State()
    date = State()
    price = State()
    finish = State()
    stop = State()


class Find_params_dialog():
    def __init__(self, database):
        self.db = database
        self.set_districts()
        self.set_dates()
        self.set_rooms()
        self.set_years()
        self.set_prices()
        self.states_group = Find_params_states()
        self.dialog = self.get_dialog()

    def get_dialog(self):
        return Dialog(
            Window(
                Const("Выбор района города:"),
                self.districts,
                Button(Const('Выбрать комнаты'), id='go_to_rooms', on_click=self.check_district_before),
                Cancel(Const("Отмена")),
                state=self.states_group.district,
            ),
            Window(
                Const("Выбрать количество комнат:"),
                self.rooms,
                Row(
                    Back(Const("Назад")),
                    Button(Const('Возраст дома'), id='go_to_years', on_click=self.check_rooms_before),
                ),
                Cancel(Const("Отмена")),
                state=self.states_group.room,
            ),
            Window(
                Const("Выбор возраста дома"),
                self.years,
                Back(Const("Назад")),
                Button(Const("Дата объявления"), id="go_to_date", on_click=self.check_years_before, ),
                Cancel(Const("Отмена")),
                state=self.states_group.year,
            ),
            Window(
                Const("Дата размещения объявления"),
                self.dates,
                Back(Const("Назад")),
                Button(Const("Цена за месяц"), id="go_to_finish", on_click=self.check_date_before, ),
                Cancel(Const("Отмена")),
                state=self.states_group.date,
            ),
            Window(
                Const("Цена в TL, 0 - без фильтра."),
                self.prices,
                Back(Const("Назад")),
                Button(Const("Закончить"), id="go_to_finish", on_click=self.check_price_before, ),
                Cancel(Const("Отмена")),
                state=self.states_group.price,
            ),
            Window(
                Const("Настройка завершена!"),
                Back(Const("Нет, я хочу вернуться и подправить фильтры.")),
                Button(Const("Да, всё готово!"), id="go_to_finish", on_click=self.finish, ),
                state=self.states_group.finish,
            )
        )

    def set_districts(self):
        self.district = [
            ("Муратпаша", 'address_town=83&'),
            ("Кепез", 'address_town=84&'),
            ("Коньялты", 'address_town=85&'),
            ("Аксу", 'address_town=86&'),
        ]
        self.districts = Multiselect(
            Format("✓ {item[0]}"),
            Format("{item[0]}"),
            id="s_districts",
            item_id_getter=operator.itemgetter(1),
            items=self.district,
        )

    def set_rooms(self):
        self.room = [
            ('1+1', 'a20=38473&'),
            ('1.5+1', 'a20=1206094&'),
            ('2+0', 'a20=1213206&'),
            ('2+1', 'a20=38470&'),
            ('3+0', 'a20=1259450&')
        ]
        self.rooms = Multiselect(
            Format("✓ {item[0]}"),
            Format("{item[0]}"),
            id="s_rooms",
            item_id_getter=operator.itemgetter(1),
            items=self.room,
        )

    def set_years(self):
        self.year = [
            ('0year', 'a812=40728&'),
            ('1year', 'a812=40602&'),
            ('2year', 'a812=40603&'),
            ('3year', 'a812=40604&'),
            ('4year', 'a812=40605&'),
            ('10year', 'a812=40606&')
        ]
        self.years = Multiselect(
            Format("✓ {item[0]}"),
            Format("{item[0]}"),
            id="s_years",
            item_id_getter=operator.itemgetter(1),
            items=self.year,
        )

    def set_dates(self):
        self.date = [
            ('24 часа', 'date=1day&'),
            ('3 дня', 'date=3days&'),
            ('7 дней', 'date=7days&'),
            ('15 дней', 'date=15days&'),
            ('30 дней', 'date=30days&'),
        ]
        self.dates = Radio(
            Format("🔘 {item[0]}"),
            Format("◯ {item[0]}"),
            id="s_dates",
            item_id_getter=itemgetter(1),
            items=self.date,
        )

    def set_prices(self):
        self.price = [
            ('0', '&'),
            ('5', 'price_max=5000&'),
            ('10', 'price_max=10000&'),
            ('15', 'price_max=15000&'),
            ('20', 'price_max=20000&'),
            ('25', 'price_max=25000&'),
            ('30', 'price_max=30000&'),
        ]
        self.prices = Radio(
            Format("🔘 {item[0]}"),
            Format("◯ {item[0]}"),
            id="s_prices",
            item_id_getter=itemgetter(1),
            items=self.price,
        )

    async def check_district_before(self, c: CallbackQuery, button: Button, manager: DialogManager):
        if self.districts.get_checked(manager):
            await self.dialog.next(manager)

    # Проверка выбранных комнат перед сменой окна
    async def check_rooms_before(self, c: CallbackQuery, button: Button, manager: DialogManager):
        if self.rooms.get_checked(manager):
            await self.dialog.next(manager)

    # Проверка выбранного возраста здания перед сменой окна
    async def check_years_before(self, c: CallbackQuery, button: Button, manager: DialogManager):
        if self.years.get_checked(manager):
            await self.dialog.next(manager)

    # Проверка выбранной даты размещения перед сменой окна
    async def check_date_before(self, c: CallbackQuery, button: Button, manager: DialogManager):
        if self.dates.get_checked(manager):
            await self.dialog.next(manager)

    # Проверка выбранной цены
    async def check_price_before(self, c: CallbackQuery, button: Button, manager: DialogManager):
        if self.prices.get_checked(manager):
            await self.dialog.next(manager)

    # Сборка URL поиска по полученным параметрам
    async def finish(self, c: CallbackQuery, button: Button, manager: DialogManager):
        base_url = 'https://www.sahibinden.com/kiralik-daire?pagingSize=50&'
        base_url += self.dates.get_checked(manager)
        for district in self.districts.get_checked(manager):
            base_url += district
        for room in self.rooms.get_checked(manager):
            base_url += room
        for year in self.years.get_checked(manager):
            base_url += year
        base_url += self.dates.get_checked(manager)
        base_url += self.prices.get_checked(manager)
        self.db.add_search_url(manager.event.from_user.id, base_url)
        await manager.done()
