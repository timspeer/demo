'''common methods'''
import os
import sys
import configparser
from datetime import datetime
import traceback
import sqlite3
from fnmatch import fnmatch
import sqlalchemy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', "Globals")))
from send_email import send_email

CONFIG_FILE = r'#REMOVED#'

class FileProcess():
    '''
    process ==> the name of the process from the config.dale file
    bypass ==> this is used to report an error then continue without breaking
    test ==> this will cause the script to ignore the filetracking database
    '''
    def __init__(self, process : str, bypass : bool=False, test : bool=False):
        self.process = process
        self.section, self.common = self.config()
        self.test = test
        self.bypass = bypass
        self.date = datetime.today().strftime("%Y-%m-%d")
        self.meta, self.engine, self.conn = self.sql_encounter()
        self.root = os.path.join(self.common['server'], self.section['root'])
        self.global_repo = os.path.join(self.common['server'], self.common['global'])
        self.common_path = os.path.join(self.common["server"], self.common['common'])
        self.db = os.path.join(self.common_path, "filetracker.db")
        self.traceback = traceback
        self.sqlalchemy = sqlalchemy
        self.send_email = send_email

    def config(self):
        '''settings'''
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        client = dict(config.items(self.process))
        common = dict(config.items("COMMON"))

        return client, common

    def check(self, table : str, filepath : str):
        '''
        check in db
        table ==> name of table used to track
        filepath ==> searches through this directory for files no in the db
        '''
        file_list = os.listdir(filepath)
        conn = sqlite3.connect(self.db)
        conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT)')
        check = conn.execute(f"SELECT Filename FROM {table}").fetchall()
        check = ["".join(item) for item in check]
        if self.test:
            check = []
        file_list = [os.path.join(filepath, item) for item in file_list if item not in check]
        file_list = [item for item in file_list if not os.path.isdir(item) and not fnmatch(item, "*.log")]
        conn.close()
        return file_list

    def track_files(self, name : str, table : str, basename : bool=True):
        '''track files in db'''
        if basename:
            name = os.path.basename(name)
        if self.test:
            return
        conn = sqlite3.connect(self.db)
        conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT)')
        conn.execute(f'INSERT INTO {table} VALUES (?,?)', (name, self.date))
        conn.commit()
        conn.close()
    
    @staticmethod
    def query(statement : list):
        text = sqlalchemy.text(" ".join(statement))
        return text

    @staticmethod
    def sql_encounter():
        '''new db methods'''
        meta = sqlalchemy.MetaData()
        engine = sqlalchemy.create_engine('#REMOVED#', isolation_level='READ UNCOMMITTED')
        conn = engine.connect()

        return meta, engine, conn

