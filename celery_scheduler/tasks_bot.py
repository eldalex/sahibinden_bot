import os
import sys
sys.path.append(os.path.abspath('../dbcontrolpack'))
sys.path.append(os.path.abspath('../parser'))
sys.path.append(os.path.abspath('../database'))
sys.path.append(os.path.abspath('../analyse_func'))

import requests
from dotenv import load_dotenv
from celery_bot import app
from db_control import Db_controller
from sahibinden_pars import Sahibinden_parser
from analyse import get_analyse_url

load_dotenv(override=True)
token = os.environ.get('TOKEN')
base_url = 'https://api.telegram.org/bot'

@app.task
def start_find(id):
    parser, db = get_connect()
    result = parser.start_search(id)
    if result:
        send_final_message(id, "Поиск успешно завершён")
    else:
        send_final_message(id, "К сожалению что то пошло не так.")
    db.close_connection()

@app.task
def add_analyse_point(id):
    try:
        parser, db = get_connect()
        get_analyse_url(id, parser, db)
        db.close_connection()
        return True
    except:
        return False


def send_final_message(chatid, message):
    url = f"{base_url}{token}/sendMessage?parse_mode=HTML"
    requests.post(url, data={
        "chat_id": chatid,
        "text": message
    })


def get_connect():
    db = Db_controller(celery=True)
    parser = Sahibinden_parser(db)
    return parser, db

