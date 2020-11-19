import sys
from types import MethodType
import psycopg2
import psycopg2.extensions
from tigaserver_project import settings as conf

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

# host = "161.111.254.244"
#Apparently unused
#_HOST = 'http://humboldt.ceab.csic.es'
#_HOST_ip = "158.109.46.21"  # posrgresql ver 1.18.1
_HOST_ip = conf.DATABASES['default']['HOST']  # posrgresql ver 1.18.1
_DB_USER = conf.DATABASES['default']['USER']
_DB_PASSWORD = conf.DATABASES['default']['PASSWORD']
_DB_NAME = conf.DATABASES['default']['NAME']
_DB_PORT = conf.DATABASES['default']['PORT']
#Apparently unused
#_LOCAL_data = '/home/jgarriga/mosquitoAlert/data/'


# +++ mosquitoAlert data base connect/disconnect functions

def connect():
    dbConn = psycopg2.connect(host=_HOST_ip, user=_DB_USER, password=_DB_PASSWORD, database=_DB_NAME, port=_DB_PORT)
    return dbConn


def disconnect(dbConn):
    dbConn.close()
    return


# +++ psycopg2.extensions.cursor extended class

class Cursor(psycopg2.extensions.cursor):
    def rowInstance(self):
        iRow = {}
        for field, rowValue in zip(self.description, self.fetchone()):
            iRow[field.name] = rowValue
        return iRow

    def browse(self, rows=0):
        if not rows: rows = self.rowcount
        for row in range(rows):
            if self.rownumber < self.rowcount:
                print
                print ('+++ %s' % str(self.rownumber).zfill(6))
                for field, fieldValue in zip(self.description, self.fetchone()):
                    print (field.name, ':', fieldValue)


# +++ mosquitoAlert Table Class

class Table:
    def __init__(self, dbConn, alias, interactive=False):

        self.alias = alias
        self.interactive = interactive
        self.getName()
        self.getCursor(dbConn)

    def getName(self):
        if self.alias == 'tUsers':
            self.name = 'tigaserver_app_tigauser'
        elif self.alias == 'tReports':
            self.name = 'tigaserver_app_report'
        elif self.alias == 'tImages':
            self.name = 'tigaserver_app_photo'
        elif self.alias == 'tNotifis':
            self.name = 'tigaserver_app_notification'
        elif self.alias == 'tResponse':
            self.name = 'tigaserver_app_reportresponse'
        elif self.alias == 'tValidate':
            self.name = 'tigacrafting_expertreportannotation'

    def getCursor(self, dbConn):
        self.cursor = dbConn.cursor()
        self.cursor.execute('select * from %s' % self.name)
        self.fList = self.cursor.description

    def fieldNames(self):
        for index, field in enumerate(self.fList):
            print (str(index).zfill(2), '.', field.name)

    def selectAll(self):
        self.cursor.execute('select * from %s;' % self.name)
        if self.interactive: print ('+++ totalRows:%6.0i' % self.cursor.rowcount)

    def selectKey(self, keyName, keyValue):
        sql = 'select * from %s where %s = ' % (self.name, keyName) + '(%s);'
        self.cursor.execute(sql, (keyValue,))
        if self.interactive: print ('+++ totalRows:%6.0i' % self.cursor.rowcount)

    def printRow(self, row):
        print
        print ('+++ %s' % str(self.cursor.rownumber).zfill(6))
        for field, rowValue in zip(self.fList, row):
            print (field.name, ':', rowValue)

    def browse(self, rows=1):
        for row in range(rows):
            if self.cursor.rownumber < self.cursor.rowcount:
                self.printRow(self.cursor.fetchone())

    def instance(self, row):
        instance = {}
        for field, rowValue in zip(self.fList, row):
            instance[field.name] = rowValue
        return instance
