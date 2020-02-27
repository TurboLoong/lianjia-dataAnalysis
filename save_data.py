import pandas as pd
import pymysql


class SaveData:
    keys = ['housecode', 'name', 'line', 'station', 'residential', 'area', 'type', 'houseArea',
            'orientation', 'decoration', 'floor', 'buildingTime', 'buildingType', 'follow',
            'unitPrice', 'totalPrice', 'tags', 'href', 'elevator', 'tradeProperty', 'farFromStation']

    def __init__(self, type=''):
        if type == 'mysql':
            self.mySqlDB = pymysql.connect(host='localhost', user='root', password='xyl2312987772', port=3306,
                                           db='lianjia')
        self.total = 0

    def save_to_mysql(self, house_list):
        cursor = self.db.cursor()
        result = []
        first = house_list[0]
        keys = ', '.join(self.keys)
        values = ', '.join(['%s'] * len(self.keys))
        sql = 'INSERT INTO house({keys}) VALUES ({values}) ON DUPLICATE KEY UPDATE '.format(keys=keys,
                                                                                            values=values)
        update = ', '.join(["{key} = %s".format(key=key) for key in self.keys])
        sql += update
        for house in house_list:
            result.append(house * 2)
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
                          columns=self.keys)
        df.to_csv('Lianjia_project.csv', mode='a', encoding='utf_8_sig', index=False)
        self.total += len(house_list)
        print(len(house_list))
        print('已插入记录数', self.total)

    def close_DB(self):
        self.db.close()
