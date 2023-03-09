import os
import sys
import numpy as np
sys.path.append(os.path.abspath('../dbcontrolpack'))
# sys.path.append(os.path.abspath('../parser'))
# sys.path.append(os.path.abspath('../database'))
# sys.path.append(os.path.abspath('../analyse_func'))
import time
# from dbcontrolpack.db_control import Db_controller
# from parser.sahibinden_pars import Sahibinden_parser
import re


def get_analyse_url(id,parser,db):
    url = db.get_analyse_url(id)
    all_apps = parser.get_current_url_appartments(url[1])
    list_price = []
    summ = 0
    for app in all_apps:
        list_price.append(int(re.sub("\D", '', app['price'])))
        summ += int(re.sub("\D", '', app['price']))
    list_price = sorted(list_price)
    average_price = round(summ / len(list_price))
    median_price = list_price[round(len(list_price) / 2)]
    minimum_price = list_price[0]
    maximum_price = list_price[-1]
    db.save_point_to_base(url[0], minimum_price, maximum_price, average_price, median_price, len(all_apps))
    print('stop')

# def fake_analys(id):
#     for i in range(5, -1, -1):
#         print(f'Работаем ещё {i} секунд')
#         print(f'{id}')
#         time.sleep(1)
#     return 'ok'
#

def get_graph(id,db):
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    data=db.get_analyse_graph(id)
    min_price_list=[]
    max_price_list=[]
    avg_price_list=[]
    med_price_list=[]
    count_ads_list=[]
    date_list=[]
    description=data[0][6]
    position = np.arange(len(date_list))
    for point in data:
        if point[5].split(' ')[0] not in date_list:
            min_price_list.append(point[0])
            max_price_list.append(point[1])
            avg_price_list.append(point[2])
            med_price_list.append(point[3])
            count_ads_list.append(point[4])
            date_list.append(point[5].split(' ')[0])
    all_graph=[min_price_list,max_price_list,avg_price_list,med_price_list]
    mpl.use('TkAgg')  # !IMPORTANT
    fig, ax = plt.subplots(figsize=(10,7))
    for graph in all_graph:
        ax.set_title(description.replace('\r','').replace('\n',' '))
        res = ax.plot(date_list, graph)  # Plt some data on the axes.o

    labels = date_list
    point=len(labels)-4
    for i in range(len(labels)-2,-1,-1):
        if i==point:
            point-=3
        else:
            labels[i]=''

    ax.set_xticklabels(labels)
    plt.xticks(rotation=20)
    plt.grid(True)
    plt.legend([f"Минимальная цена: последние данные:({min_price_list[-1]})", f"Максимальная цена: последние данные:({max_price_list[-1]})", f"Средняя цена: последние данные:({avg_price_list[-1]})", f"Медианная цена: последние данные:({med_price_list[-1]})"],loc="lower left")
    # plt.autoscale=True
    # plt.show() # optionally show the result.
    return fig
    # fig.savefig('мой график')

