# coding: UTF-8
'''
Created on 2012-7-13
@author: admin
'''
import MySQLdb
import mylog as log
import numpy as np

class DBUtil:
    
    def __init__(self):
        '''
        默认连接
        '''
        self.connectDB = self.connector_DB14_tansat
        
    def setDBConnector(self, dbConnectorFunc):
        '''
        设定连接DB所用函数
        '''
        self.connectDB = dbConnectorFunc

    def connector_DB14_tansat(self):
        '''
        Create connection to 10.24.185.14, MySQL tansat DB.
        '''
        db = MySQLdb.connect(host='10.24.185.14', user='root', passwd='gsics12332', db='tansat', use_unicode = True, charset = "utf8")
        return db

    def connector_DB110_gsics(self):
        '''
        建立和数据库系统的连接  
        '''
        db = MySQLdb.connect(host='10.0.66.33', user='root', passwd='gsics110', db='gsics', use_unicode = True, charset = "utf8") 
#         db = MySQLdb.connect(host='10.24.0.69', user='root', passwd='gsics12332', db='gsics', use_unicode = True, charset = "utf8") 
        return db
            
    def connector_DB110(self):
        '''
        建立和数据库系统的连接  
        '''
        db = MySQLdb.connect(host='10.0.66.33', user='root', passwd='gsics110', db='fy_system', use_unicode = True, charset = "utf8")  
        return db

    def executeSearch(self, sql):
        '''
        检索DB
        '''
        db = self.connectDB()
        cursor = db.cursor()
        count = 0
        results = ()
        try:
            count = cursor.execute(sql)
            if count > 0:
                results = cursor.fetchall()
        except Exception,e:
            log.error('sql:%s, error:%s' % (sql, e))
        finally:
            cursor.close()
            db.close()
        return results
    
    def executeInsert(self, sql, params=[]):
        '''
        插入DB，一行or多行
        '''
        db = self.connectDB()
        cursor = db.cursor()
        try:
            if len(params) == 0:
                cursor.execute(sql)
            elif len(np.array(params).shape) == 2: 
                cursor.executemany(sql, params)
            else:
                return
            db.commit()
        except Exception,e:
            db.rollback()
            log.error('sql:%s, error:%s' % (sql, e))
        finally:
            cursor.close()
            db.close()
    
    def executeUpate(self, sql):
        '''
        更新DB一条记录
        '''
        db = self.connectDB()
        cursor = db.cursor()
        try:
            cursor.execute(sql)
            db.commit()
        except Exception,e:
            db.rollback()
            log.error('sql:%s, error:%s' % (sql, e))
        finally:
            cursor.close()
            db.close()
            
    def executeDelete(self, sql):
        '''
        删除DB记录
        '''
        self.executeUpate(sql)
        
if __name__=='__main__':
    pass
