from configobj import ConfigObj

import os
import sys
import DB_Sql

localpath = os.path.split(os.path.realpath(__file__))[0]
localcfg = os.path.join(localpath, 'tan_sql.cfg')
Cfg = ConfigObj(localcfg)

def main():

    DATATYPE_PATH = Cfg['datatype']['PATH']
    lst = txt2list(DATATYPE_PATH)
    DB_Sql.insertTbl_datatype(lst)

    jkl

def addln2list(filename):
    pass

def txt2list(filename):
    '''
    Read from txt file to 2-dimensions list
    '''
    try:
        with open(filename) as f:
            mylist = f.read().splitlines()
    except Exception as e:
        e = sys.exc_info()[0]
        print e.__doc__
        print e.message
        sys.exit(1)
    else:
        mylist_2 = []

        for i in range(len(mylist)):
            mylist_2.append(mylist[i].split())

        return mylist_2

if __name__ == '__main__':
    main()
