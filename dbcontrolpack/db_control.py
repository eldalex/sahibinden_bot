import sqlite3


class Db_controller():
    def __init__(self, celery=False):
        self.connection = sqlite3.connect('database\\sahibinden.db') if not celery else sqlite3.connect(
            '..\\database\\sahibinden.db')

    def close_connection(self):
        self.connection.close()

    def get_cursor(self):
        return self.connection.cursor()

    def create_table(self):
        with self.connection:
            try:
                cursor = self.get_cursor()
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS  USERS_BOT ("
                    f"user_id INTEGER NOT NULL PRIMARY KEY,"
                    f"username TEXT,"
                    f"first_name TEXT,"
                    f"last_name TEXT,"
                    f"reg_date DATE)"
                )
                self.connection.commit()
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS  USERS_FIND_PARAMS ("
                    f"id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                    f"user_id INTEGER,"
                    f"url TEXT,"
                    f"FOREIGN KEY (user_id) "
                    f"  REFERENCES USERS_BOT(user_id)"
                    f"    ON DELETE CASCADE"
                    f"    ON UPDATE NO ACTION"
                    f")"
                )
                self.connection.commit()
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS  ALL_RESULTS ("
                    f"app_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                    f"url TEXT,"
                    f"thumbnail_url TEXT,"
                    f"area INTEGER,"
                    f"rooms TEXT,"
                    f"price TEXT,"
                    f"date TEXT,"
                    f"district TEXT"
                    f")"
                )
                self.connection.commit()
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS  USERS_FIND_RESULT ("
                    f"id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                    f"user_id INTEGER,"
                    f"app_id INTEGER,"
                    f"FOREIGN KEY (user_id) "
                    f"  REFERENCES USERS_BOT(user_id)"
                    f"    ON DELETE CASCADE"
                    f"    ON UPDATE NO ACTION,"
                    f"FOREIGN KEY (app_id) "
                    f"  REFERENCES ALL_RESULTS(app_id)"
                    f"    ON DELETE CASCADE"
                    f"    ON UPDATE NO ACTION"
                    f")"
                )
                self.connection.commit()
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS  USERS_FAVORITE_APP ("
                    f"id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                    f"user_id INTEGER,"
                    f"app_id INTEGER,"
                    f"FOREIGN KEY (user_id) "
                    f"  REFERENCES USERS_BOT(user_id)"
                    f"    ON DELETE CASCADE"
                    f"    ON UPDATE NO ACTION,"
                    f"FOREIGN KEY (app_id) "
                    f"  REFERENCES ALL_RESULTS(app_id)"
                    f"    ON DELETE CASCADE"
                    f"    ON UPDATE NO ACTION"
                    f")"
                )
                self.connection.commit()
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS  SAHIBINDEN_ANALYS_URLS ("
                    f"id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                    f"url TEXT,"
                    f"description TEXT"
                    f")"
                )
                self.connection.commit()
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS  SAHIBINDEN_ANALYS_POINTS ("
                    f"id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
                    f"id_analys_url, "
                    f"minimum_price INTEGER,"
                    f"maximum_price INTEGER,"
                    f"average_price INTEGER,"
                    f"median_price INTEGER,"
                    f"count_ads INTEGER,"
                    f"point_date TEXT,"
                    f"FOREIGN KEY (id_analys_url) "
                    f"  REFERENCES SAHIBINDEN_ANALYS_URLS(id)"
                    f"    ON DELETE CASCADE"
                    f"    ON UPDATE NO ACTION"
                    f")"
                )
                self.connection.commit()

                cursor.close()
            except Exception as ex:
                print(f'create_table:   {ex}')

    def send_user_info(self, userinfo):
        cursor = self.get_cursor()
        try:
            cursor.execute(
                f"INSERT INTO USERS_BOT (user_id, username, first_name, last_name, reg_date) "
                f"VALUES({userinfo[0]},'{userinfo[1]}','{userinfo[2]}','{userinfo[3]}','{userinfo[4]}')")
        except Exception as ex:
            print(f'send_user_info:   {ex}')
        self.connection.commit()
        cursor.close()

    def delete_search_url(self, id):
        cursor = self.get_cursor()
        try:
            cursor.execute(
                f"DELETE FROM USERS_FIND_PARAMS "
                f"WHERE id={id}"
            )
        except Exception as ex:
            print(f'delete_search_url:   {ex}')
        self.connection.commit()
        cursor.close()

    def get_only_new_results(self, all_results_distinct):
        try:
            cursor = self.get_cursor()
            cursor.execute(f'SELECT app_id FROM ALL_RESULTS')
            ids = cursor.fetchall()
            cursor.close()
            already_have_ids = []
            for id in ids:
                already_have_ids.append(id[0])
            for i in range(len(all_results_distinct) - 1, -1, -1):
                if int(all_results_distinct[i]['id']) in already_have_ids:
                    all_results_distinct.pop(i)
            return all_results_distinct
        except Exception as ex:
            print(f'get_only_new_results:   {ex}')

    def save_all_result_to_base(self, all_results_distinct):
        try:
            # так как все результаты хранятся в одной таблице с идентификатором по номеру объявления, результаты разных пользователей могут пересекаться
            # отправляем их на дополнительную фильтрацию, и запишем только те что еще не присутствуют в БД
            all_results_distinct = self.get_only_new_results(all_results_distinct)
            if all_results_distinct:
                cursor = self.get_cursor()
                sql_insert_query = (f'INSERT INTO ALL_RESULTS (app_id,url,thumbnail_url,area,rooms,price,date,district) '
                                    f'VALUES ')
                for result in all_results_distinct:
                    one_value_str = f"({result['id']}, '{result['link']}', '{result['thumbnail_url']}', {result['area']}, '{result['rooms']}', '{result['price']}', '{result['date_listing']}', '{result['district']}'),"
                    sql_insert_query += one_value_str
                # Чтобы было короче, запихнём в БД одним запросом.
                cursor.execute(sql_insert_query[:-1])
                self.connection.commit()
                cursor.close()
        except Exception as ex:
            print(f'save_all_result_to_base:   {ex}')

    def get_user_urls(self, user_id):
        try:
            cursor = self.get_cursor()
            cursor.execute(
                f"SELECT id,url FROM USERS_FIND_PARAMS "
                f"WHERE user_id={user_id}"
            )
            results = cursor.fetchall()
            urls = []
            for item in results:
                urls.append(item[1])
            cursor.close()
            return urls
        except Exception as ex:
            print(f'get_user_urls:   {ex}')

    def save_all_id_for_user(self, distinct_id, user_id):
        try:
            cursor = self.get_cursor()
            cursor.execute(
                f"SELECT app_id FROM USERS_FIND_RESULT "
                f"WHERE user_id={user_id}"
            )
            ids = cursor.fetchall()
            cursor.close()
            users_app_ids = []
            for id in ids:
                users_app_ids.append(id[0])
            for i in range(len(distinct_id) - 1, -1, -1):
                if int(distinct_id[i]) in users_app_ids:
                    distinct_id.pop(i)

            if distinct_id:
                cursor = self.get_cursor()
                sql_insert_query = (f'INSERT INTO USERS_FIND_RESULT (user_id,app_id) '
                                    f'VALUES ')
                for result in distinct_id:
                    one_value_str = f"({user_id}, {result}),"
                    sql_insert_query += one_value_str
                # Чтобы было короче, запихнём в БД одним запросом.
                cursor.execute(sql_insert_query[:-1])
                self.connection.commit()
                cursor.close()
        except Exception as ex:
            print(f'save_all_id_for_user:   {ex},{distinct_id=},{user_id=}')

    def check_search_url(self, user_id, url):
        cursor = self.get_cursor()
        try:
            cursor.execute(
                f"SELECT id,url FROM USERS_FIND_PARAMS "
                f"WHERE user_id={user_id}"
            )
            results = cursor.fetchall()
            urls = []
            ids = []
            for item in results:
                urls.append(item[1])
                ids.append(item[0])
            if url in urls:
                print('такой url уже существует у данного пользователя')
                return True
            elif len(ids) >= 3:
                print('Это новый url но у пользователя уже есть три строки поиска, удаляем одну')
                self.delete_search_url(sorted(ids)[0])
                return False
            else:
                print('это новый url, и у пользователя пока меньше трёх поисков')
                return False
        except Exception as ex:
            print(f'check_search_url:   {ex}')
        self.connection.commit()
        cursor.close()

    def save_search_url(self, user_id, url):
        cursor = self.get_cursor()
        try:
            cursor.execute(
                f"INSERT INTO USERS_FIND_PARAMS(user_id,url)"
                f"VALUES ({user_id},'{url}')"
            )
        except Exception as ex:
            print(f'save_search_url:   {ex}')
        self.connection.commit()
        cursor.close()

    def add_search_url(self, user_id, url):
        if not self.check_search_url(user_id, url):
            self.save_search_url(user_id, url)
            print('добавили новую строку поиска')
        else:
            print('такой запрос уже существует. ничего не делаем.')

    def get_user_result(self, user_id, type):
        if type == 'all':
            table = 'USERS_FIND_RESULT'
        elif type == 'fav':
            table = 'USERS_FAVORITE_APP'
        try:
            cursor = self.get_cursor()
            cursor.execute(
                f"SELECT ufr.app_id, ar.url, ar.thumbnail_url, ar.area, ar.rooms, ar.price, ar.date, ar.district FROM {table} ufr, ALL_RESULTS ar "
                f"where "
                f"ufr.user_id = {user_id} "
                f"and ufr.app_id = ar.app_id "
            )
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as ex:
            print(f'get_user_result:   {ex}')

    def add_to_favorite(self, user_id, app_id):
        try:
            cursor = self.get_cursor()
            cursor.execute(f"SELECT count(*) as count from USERS_FAVORITE_APP "
                           f"where user_id={user_id} and app_id={app_id}")
            count = cursor.fetchone()
            if count[0] == 0:
                cursor.execute(
                    f"INSERT INTO USERS_FAVORITE_APP(user_id, app_id)  "
                    f"VALUES({user_id}, {app_id}) "
                )
                self.connection.commit()
            cursor.close()
        except Exception as ex:
            print(f'add_to_favorite:   {ex}')

    def delete_from_favorite(self, user_id, app_id):
        try:
            cursor = self.get_cursor()
            cursor.execute(
                f"DElETE FROM USERS_FAVORITE_APP "
                f"WHERE user_id={user_id} and app_id={app_id} "
            )
            self.connection.commit()
            cursor.close()
        except Exception as ex:
            print(f'delete_from_favorite:   {ex}')

    def get_analyse_url(self, id):
        try:
            cursor = self.get_cursor()
            cursor.execute(
                f"SELECT id,url from SAHIBINDEN_ANALYS_URLS "
                f"WHERE id = {id}"
            )
            return cursor.fetchone()
        except Exception as ex:
            print(f'get_analyse_url:   {ex}')

    def save_point_to_base(self, id, minimum_price, maximum_price, average_price, median_price, count_ads):
        try:
            cursor = self.get_cursor()
            cursor.execute(
                f"INSERT INTO SAHIBINDEN_ANALYS_POINTS(id_analys_url"
                f", minimum_price"
                f", maximum_price"
                f", average_price"
                f", median_price"
                f", count_ads"
                f", point_date) "
                f"VALUES({id}, {minimum_price}, {maximum_price}, {average_price}, {median_price}, {count_ads}, datetime('now')) "
            )
            self.connection.commit()
            cursor.close()
        except Exception as ex:
            print(f'save_point_to_base:   {ex}')

    def get_analyse_graph(self, id):
        try:
            cursor = self.get_cursor()
            cursor.execute(
                f"SELECT "
                f"sap.minimum_price, "
                f"sap.maximum_price, "
                f"sap.average_price, "
                f"sap.median_price, "
                f"sap.count_ads, "
                f"sap.point_date, "
                f"sau.description "
                f"from SAHIBINDEN_ANALYS_POINTS sap , SAHIBINDEN_ANALYS_URLS sau "
                f"where sap.id_analys_url = sau.id "
                f"and sau.id={id}"
            )
            return cursor.fetchall()
        except Exception as ex:
            print(f'get_analyse_graph:   {ex}')

    def get_id_analyse_tasks(self):
        try:
            cursor = self.get_cursor()
            cursor.execute("SELECT id,description from SAHIBINDEN_ANALYS_URLS")
            ids = cursor.fetchall()
            cursor.close()
            return ids
        except Exception as ex:
            print(f'get_id_analyse_tasks:   {ex}')
