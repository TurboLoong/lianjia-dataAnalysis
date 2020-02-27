import pandas as pd
import pymysql


class SaveToMysql:
    def __init__(self):
        self.db = pymysql.connect(host='localhost', user='root', password='xyl2312987772', port=3306, db='lianjia')
        self.total = 0

    def save_to_mysql(self, house_list):
        cursor = self.db.cursor()
        result = []
        first = house_list[0]
        keys = ', '.join(first.keys())
        values = ', '.join(['%s'] * len(first.keys()))
        sql = 'INSERT INTO house({keys}) VALUES ({values}) ON DUPLICATE KEY UPDATE '.format(keys=keys,
                                                                                            values=values)
        update = ', '.join(["{key} = %s".format(key=key) for key in first.keys()])
        sql += update
        for house in house_list:
            item = tuple(house.values()) * 2
            result.append(item)
        try:
            if cursor.executemany(sql, result):
                self.db.commit()
            else:
                print('执行sql失败')
        except:
            print('执行sql失败')
            self.db.rollback()
        self.total += len(house_list)
        print(len(house_list))
        print('已插入记录数', self.total)

    def save_to_csv(self, house_list):
        df = pd.DataFrame(house_list,
                          columns=['housecode', 'name', 'line', 'station', 'residential', 'area', 'type', 'houseArea',
                                   'orientation', 'decoration', 'floor', 'buildingTime', 'buildingType', 'follow',
                                   'unitPrice', 'totalPrice', 'tags', 'href'])
        df.to_csv('Lianjia_project.csv', index=False, encoding='utf_8_sig')

    def close_DB(self):
        self.db.close()
