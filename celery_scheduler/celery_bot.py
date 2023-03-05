import os
import sys

sys.path.append(os.path.abspath('../dbcontrolpack'))
from db_control import Db_controller

from celery import Celery
from celery.schedules import crontab
import datetime
import random

app = Celery('celery_parser')
app.config_from_object('celeryconfig')


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    app.conf.beat_schedule = get_beat_schedule(fill_slots(get_ids(), get_slots()))
    pass


def get_slots():
    schedule = []
    current = datetime.datetime.now().hour * 60 + datetime.datetime.now().minute
    for i in range(current, current + 1440, +10):
        schedule.append({"hour": i // 60 if i // 60 < 24 else i // 60 - 24,
                         "minutes": i % 60,
                         "id_url": '',
                         "description": '',
                         "taken": False})
    return schedule


def fill_slots(ids, slots):
    for id in ids:
        while True:
            slot = random.randint(1, 143)
            if slots[slot]["taken"] == False:
                slots[slot]["id_url"] = (id[0],)
                slots[slot]["description"] = id[1].replace('\r', '').replace('\n', ' ')
                slots[slot]["taken"] = True
                break
    return slots


def get_beat_schedule(filled_slots):
    beat_schedule = {}
    for i in filled_slots:
        if i['taken'] == True:
            beat_schedule.update({
                i['description']: {
                    'task': 'tasks_bot.add_analyse_point',
                    'args': i["id_url"],
                    'schedule': crontab(hour=i['hour'], minute=i['minutes']),
                }
            })

    return beat_schedule


def get_ids():
    try:
        db = Db_controller(celery=True)
        ids = db.get_id_analyse_tasks()
        return ids
    except Exception as ex:
        print(ex)
