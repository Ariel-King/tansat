import sys
import mysql.connector
from mysql.connector import errorcode

config = {
        'user': 'root',
        'password': 'gsics12332',
        'host': '127.0.0.1',
        'database': 'tansat',
        'raise_on_warnings': True,
        }

try:
    cnx = mysql.connector.connect(**config)
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
        sys.exit(1)
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
        sys.exit(1)
    else:
        print(err)
        sys.exit(1)

cur = cnx.cursor()
cur.execute("SELECT VERSION()")
print "Database version: %s" % cur.fetchone()

cnx.close()
