'''Webscraping class'''
import time
import os
import sys
import configparser
import sqlalchemy
import sqlite3
import traceback # pylint: disable=unused-import

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import JavascriptException, TimeoutException, ElementClickInterceptedException # pylint: disable=unused-import 
from selenium.webdriver.common.action_chains import ActionChains

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', "Globals")))
from send_email import send_email
from password_encryption import get_password
from psexec import psexec # pylint: disable=unused-import
from pdf_to_text import pdf_to_text # pylint: disable=unused-import

def sqlite3_select(table:str, database:os.PathLike) -> list:
    '''check for files on sftp server'''
    try:
        with sqlite3.connect(database) as conn:
            check_db:set = conn.execute(f"SELECT * FROM {table}").fetchall()
    except sqlite3.OperationalError:
        return []
    check_db:list = [list(item) for item in check_db]
    return check_db

def sqlite3_insert(table:str, dict_:dict, database:os.PathLike) -> None:
    '''track files in db'''
    key_list:list = list(dict_.keys())
    columns:str = ", ".join([item+" TEXT" for item in key_list])
    with sqlite3.connect(database) as conn:
        conn.execute(f'CREATE TABLE IF NOT EXISTS {table} ({columns})')
        conn.commit()
    
    question_marks:str = ",".join(["?" for _ in key_list])
    vals:list = []
    for key in key_list:
        vals.append(dict_[key])
    with sqlite3.connect(database) as conn:
        conn.execute(f'INSERT INTO {table} VALUES ({question_marks})', vals)
        conn.commit()

def sqlite3_delete(table:str, dict_:dict, database:os.PathLike) -> None:
    '''track files in db'''
    statement:list = []
    for key, val in dict_.items():
        statement.append(f"{key} = '{val}'")
    statement:str = " AND ".join(statement)
    with sqlite3.connect(database) as conn:
        try:
            conn.execute(f'DELETE FROM {table} WHERE {statement}')
        except sqlite3.OperationalError:
            return
        conn.commit()

def sqlite3_drop_table(table:str, database:os.PathLike) -> None:
    '''drop table'''
    with sqlite3.connect(database) as conn:
        try:
            conn.execute(f'DROP TABLE {table}')
        except sqlite3.OperationalError:
            return
        conn.commit()

class Webscrape():
    '''common methods for scraping'''
    def __init__(self, site:str, kiosk:bool=True, head:bool=False, browser_session:bool=True,
                 browser_quit=True):
        self.site = site
        self.head = head
        self.kiosk = kiosk
        self.specific, self.common = self.config()
        self.root = os.path.join(self.common['server'], self.specific['root'])
        self.chromedriver = os.path.join(os.path.dirname(os.path.realpath(__file__)), "chromedriver.exe")
        self.db = os.path.join(os.path.join(os.path.dirname(__file__), 'webscrape.db'))
        if browser_session:
            self.browser = self.generate_browser()
        self.conn = self.sql_connection()
        self.send_email = send_email
        self.username = self.specific["username"]
        self.password = get_password(self.username, self.specific['site'])
        self.browser_quit = browser_quit

    def config(self) -> tuple:
        '''settings'''
        config_file = os.path.join(os.path.dirname(__file__), 'config.dale')
        config = configparser.ConfigParser()
        config.read(config_file)
        specific = dict(config.items(self.site))
        common = dict(config.items("COMMON"))

        return specific, common

    def generate_browser(self) -> object:
        '''initialize browser'''
        options:object = Options()
        options.add_argument(f"user-data-dir=C:\\Web Scraping Profiles\\{self.site}")
        options.add_argument("start-maximized")
        if self.kiosk:
            options.add_argument("--kiosk-printing")
        if not self.head:
            options.add_argument("--headless")
        options.add_experimental_option("detach", True)
        browser:object = webdriver.Chrome(self.chromedriver, options=options)
        return browser

    def click(self, xpath : str, pause: int=10, node : object=None) -> object:
        '''click element by xpath'''
        if not node:
            node:object = self.browser
        self.wait(xpath, pause, node)
        time.sleep(.5)
        try:
            return_node = node.find_element_by_xpath(xpath)
            return_node.click()
        except TimeoutException:
            self.browser.execute_script("arguments[0].scrollIntoView();", self.browser.find_element_by_xpath(xpath))
            ActionChains(self.browser).move_to_element(node.find_element_by_xpath(xpath)).perform()
            time.sleep(.5)
        return return_node

    def wait(self, xpath : str, duration : int=10, node : object=None) -> object:
        '''wait for element'''
        if not node:
            node:object = self.browser
        time.sleep(.5) 
        WebDriverWait(node, duration).until(EC.presence_of_element_located((By.XPATH, xpath)))
        time.sleep(.5)
        return node
        
    def switch(self, *args : str, duration : int=10):
        '''switch frames'''
        self.browser.switch_to.default_content()
        if args:
            for arg in args:
                self.wait(arg, duration)
                self.browser.switch_to.frame(self.browser.find_element_by_xpath(arg))
    
    def key(self, xpath : str, text : str, duration : int=10, node : object=None) -> object:
        '''key in field'''
        if not node:
            node:object = self.browser
        self.wait(xpath, duration, node)
        return_node = node.find_element_by_xpath(xpath)
        return_node.send_keys(text)
        time.sleep(.5)
        return return_node

    def return_text(self, xpath : str, duration : int=10, node : object=None) -> tuple:
        '''returns text from screen'''
        if not node:
            node:object = self.browser
        self.wait(xpath, duration, node)
        return_node = node.find_element_by_xpath(xpath)
        text = return_node.text
        time.sleep(.5)
        return text, return_node

    def script(self, steps : list, duration : int=5) -> str:
        '''execute javascript'''
        steps = ";".join(steps)
        check = False
        count = 0
        while check is False:
            time.sleep(duration)
            try:
                r_val = self.browser.execute_script(steps)
                check = True
            except JavascriptException as exception:
                count += 1
                if count == 4:
                    raise exception
        return r_val

    @staticmethod
    def sql_connection():
        '''create sql connection'''
        engine = sqlalchemy.create_engine('#REMOVED#')
        conn = engine.connect()
        return conn
