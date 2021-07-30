'''common methods'''
import os
import sys
import configparser
from datetime import datetime
import traceback
import sqlite3
from fnmatch import fnmatch
import sqlalchemy
import filecmp
import shutil
import re

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
        self.db = os.path.join(self.common_path, "filetrack.db")
        self.traceback = traceback
        if self.sync_modules() == "Reload":
            os.execl(sys.executable, *([sys.executable]+sys.argv))
        if self.pull_globals() == "Reload":
            os.execl(sys.executable, *([sys.executable]+sys.argv))

    def config(self):
        '''settings'''
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        client = dict(config.items(self.process))
        common = dict(config.items("COMMON"))

        return client, common

    def pull_globals(self):
        '''pull globals'''
        global_list  = self.common["global_list"].split(",")
        current_file = os.path.join(os.path.dirname(__file__), __file__)
        for item in global_list:
            replacement_text = ''
            filepath = os.path.join(self.global_repo, item+".py")
            with open(filepath, 'r') as infile:
                init_text = infile.read()
                sections = f"#{item}"
                text = re.findall(fr'{sections}[\s\S]*?{sections}', init_text)[0]
            with open(current_file, 'r') as current:
                current_text = current.read()
                if text not in current_text:
                    replacement_text = re.sub(fr'{sections}[\s\S]*?{sections}', "", current_text)
                    replacement_text = replacement_text+"\n\n"+text
            if replacement_text:
                with open(current_file, 'w') as outfile:
                    outfile.write(replacement_text)
                    return "Reload"

    def sync_modules(self):
        '''sync modules with'''
        current_module = os.path.join(os.path.dirname(__file__), __file__)
        sync_module = os.path.join(self.common_path, "methods.py")
        if not filecmp.cmp(current_module, sync_module):
            os.remove(current_module)
            shutil.copy2(sync_module, current_module)
            return "Reload"

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


if __name__ == "__main__":
    FileProcess("MTRX_Compensation")