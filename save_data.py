import pandas as pd
import pymysql


class SaveToMysql:
    def __init__(self, type):
        if (type != 'csv'):
            self.db = pymysql.connect(host='localhost', user='root', password='xyl2312987772', port=3306, db='lianjia')

    def save_to_mysql(self, house_list):
        cursor = self.db.cursor()
        for house in house_list:
            keys = ', '.join(house.keys())
            values = ', '.join(['%s'] * len(house))
            sql = 'INSERT INTO house({keys}) VALUES ({values}) ON DUPLICATE KEY UPDATE '.format(keys=keys,
                                                                                                values=values)
            update = ', '.join(["{key} = %s".format(key=key) for key in house])
            sql += update
            result = tuple(house.values()) * 2
            try:
                if cursor.execute(sql, result):
                    self.db.commit()
            except:
                print('fail')
                self.db.rollback()
        self.db.close()

    def save_to_csv(self, house_list):
        df = pd.DataFrame(house_list,
                          columns=['housecode', 'name', 'line', 'station', 'residential', 'area', 'type', 'houseArea',
                                   'orientation', 'decoration', 'floor', 'buildingTime', 'buildingType', 'follow',
                                   'unitPrice', 'totalPrice', 'tags', 'href'])
        df.to_csv('Lianjia_project.csv', index=False, encoding='utf_8_sig')
