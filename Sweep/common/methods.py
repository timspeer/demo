'''common methods'''
import configparser
import os
import sys
import json
import shutil
import requests
from datetime import datetime
import re
import urllib.parse
import sqlite3
import typing
import traceback # pylint: disable=unused-import

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', "Globals")))
from send_email import send_email
from password_encryption import get_password

class Sweep():
    '''
    sweep_name => name of sweep in config file
    bypass => continue and report on error
    test => ignore database
    '''
    def __init__(self, sweep_name : str, bypass : bool=True, test : bool=False, custom_destination:bool=False):
        self.sweep_name:str = sweep_name
        self.sweep:dict
        self.common:dict
        self.sweep, self.common = self.config()
        self.test:bool = test
        self.bypass:bool = bypass
        self.token:json = self.authenticate()
        self.files:list = self.get_files()
        if custom_destination:
            self.destination:os.PathLike =\
                os.path.join(self.common["server"], self.sweep['destination'])
        else:
            self.destination:os.PathLike =\
                os.path.join(self.common["server"], self.common['destination'])
        self.pattern:str = self.sweep['pattern'].replace("&", "%26")
        self.date:str = datetime.now().strftime("%Y-%m-%d")
        self.send_email:typing.Callable = send_email

    def config(self) -> typing.Tuple[dict, dict]:
        '''setup and file transport'''
        config_file:os.PathLike = os.path.join(os.path.dirname( __file__ ) ,'config.dale')
        config:object = configparser.ConfigParser()
        config.read(config_file)
        client:dict = dict(config.items(self.sweep_name))
        common:dict = dict(config.items("COMMON"))
        return client, common

    def get_files(self, database=None) -> list:
        '''get list of doctors'''
        if not database:
            database:os.PathLike=os.path.join(os.path.dirname(__file__), "filetracker.db")
        conn = sqlite3.connect(database)
        conn.execute(f'CREATE TABLE IF NOT EXISTS {self.sweep["table"]} (Filename TEXT, Date TEXT)')
        check = conn.execute(f'SELECT Filename FROM {self.sweep["table"]}').fetchall()
        check = ["".join(item) for item in check]
        conn.close()
        return check

    def track_files(self, name:str, database=None) -> None:
        '''get list of doctors'''
        if self.test:
            return
        if not database:
            database:os.PathLike = os.path.join(os.path.dirname(__file__), "filetracker.db")
        conn:object = sqlite3.connect(database)
        conn.execute(f'CREATE TABLE IF NOT EXISTS {self.sweep["table"]} (Filename TEXT, Date TEXT)')
        conn.execute(f'INSERT INTO {self.sweep["table"]} VALUES (?,?)', (name, self.date))
        conn.commit()
        conn.close()

    def authenticate(self) -> json:
        '''authenticate session'''
        client_id:str = get_password("ClientID", "Sharefile API")
        client_secret:str = get_password("ClientSecret", "Sharefile API")
        password:str = get_password(self.common["username"], "Sharefile API")

        token_url:str = urllib.parse.urljoin(self.common["url"], "/oauth/token")
        headers:dict = {'Content-Type' : 'application/x-www-form-urlencoded'}
        data:dict = {
            'grant_type' : 'password',
            'username' : self.common["username"],
            'password' : password,
            }
        response:object = requests.post(
            token_url,
            data=data,
            verify=True,
            auth=(client_id, client_secret),
            headers=headers
            )
        if response.status_code == 200:
            token = json.loads(response.text)
        else:
            self.send_email(
                "Authentication Error:\n\nCheck/Reset Sharefile Credentials and API Password",
                "Sharefile API Authentication Error"
                )
            raise Exception("Authentication Error")
        return token

    def check_files(self) -> list:
        '''get list of files'''
        uri_parts:list = [
            'https://#REMOVED#.sf-api.com/sf/v3/Items(allshared)/ByPath?path=/',
            f'{self.pattern}&$expand=Children'
        ]
        uri_path:str = "".join(uri_parts)

        response:object = requests.get(
            uri_path,
            headers={'Authorization' : f'Bearer {self.token["access_token"]}'}
            )
        response_list:list = list(json.loads(response.text)['Children'])

        return_list:list = [{"ID":item["Id"], "Name":item["Name"]} for item in response_list]

        return return_list

    def download_files(self, file_list:list=None):
        '''download files'''
        if not file_list:
            file_list:list = self.check_files()
        track_list:list = file_list.copy()
        if not self.test:
            file_list:list = [item for item in file_list if item["Name"] not in self.files]
        for item in file_list:
            #if item["Name"] not in track_list:
            #    self.track_files(item["Name"])
            uri_path = f'https://#REMOVED#.sf-api.com/sf/v3/Items({item["ID"]})/Download'
            with requests.get(
                uri_path,
                stream=True,
                headers={'Authorization' : f'Bearer {self.token["access_token"]}'},
                allow_redirects=True
                ) as response:
                filename = os.path.join(self.destination, self.sweep_name+"_"+item["Name"])
                with open(filename, 'wb') as target:
                    shutil.copyfileobj(response.raw, target)
                if item["Name"] not in track_list:
                    self.track_files(item["Name"])

    def move_files(self, target:str):
        '''move file from one folder to another'''
        uri_parts:list = [
            'https://#REMOVED#.sf-api.com/sf/v3/Items(allshared)/ByPath?path=/',
            f'{self.pattern}&$expand=Children'
        ]
        uri_path:str = "".join(uri_parts)

        response:object = requests.get(
            uri_path,
            headers={'Authorization' : f'Bearer {self.token["access_token"]}'}
            )
        response_list:list = list(json.loads(response.text)['Children'])

        response_list:list = [{"ID":item["Id"], "Name":item["Name"]} for item in response_list]

        target_id:str = [response_list.pop(idx) for idx, item in enumerate(response_list)
                         if item["Name"] == target][0]

        for item in response_list:
            post_parts:list = [
                f'https://#REMOVED#.sf-api.com/sf/v3/Items({item["ID"]})/',
                f'Copy?targetid={target_id["ID"]}&overwrite=true'
            ]
            post_uri:str = "".join(post_parts)
            headers = {
                'Authorization' : f'Bearer {self.token["access_token"]}',
                "Content-Type" : "application/json"
            }
            response:object = requests.post(post_uri, headers=headers)
            delete_path:str = f'https://#REMOVED#.sf-api.com/sf/v3/Items({item["ID"]})'
            response:object = requests.delete(delete_path, headers=headers)

    def dir_walk(self, skip:list=None):
        '''walk through directories'''
        file_list:list = self.check_files()
        track_list:list = file_list.copy()
        if not self.test:
            file_list:list = [item for item in file_list if item["Name"] not in self.files]
        item:set
        for item in file_list:
            if re.match(r'.*\.[a-zA-Z]{3}', item['Name']):
                #if item["Name"] not in track_list:
                #    self.track_files(item["Name"])
                uri_path = f'https://#REMOVED#.sf-api.com/sf/v3/Items({item["ID"]})/Download'
                with requests.get(
                    uri_path,
                    stream=True,
                    headers={'Authorization' : f'Bearer {self.token["access_token"]}'},
                    allow_redirects=True
                    ) as response:
                    filename = os.path.join(self.destination, self.sweep_name+"_"+item["Name"])
                    with open(filename, 'wb') as target:
                        shutil.copyfileobj(response.raw, target)
                    if item["Name"] not in track_list:
                        self.track_files(item["Name"])
            else:
                new_token:str = None

                dir_name:str = item["Name"]

                if skip and dir_name in skip:
                    continue

                uri_parts:list = [
                    f'https://#REMOVED#.sf-api.com/sf/v3/Items({item["ID"]})?$expand=Children'
                ]
                uri_path:str = "".join(uri_parts)

                try:
                    response:object = requests.get(
                        uri_path,
                        headers={'Authorization' : f'Bearer {self.token["access_token"]}'},
                        allow_redirects=True
                        )
                except requests.exceptions.ConnectionError:
                    new_token:str = self.authenticate()["access_token"]
                    response:object = requests.get(
                        uri_path,
                        headers={'Authorization' : f'Bearer {new_token}'},
                        allow_redirects=True
                        )
                try:
                    response_list:list = list(json.loads(response.text)['Children'])
                except json.decoder.JSONDecodeError:
                    new_token:str = self.authenticate()["access_token"]
                    response:object = requests.get(
                        uri_path,
                        headers={'Authorization' : f'Bearer {new_token}'},
                        allow_redirects=True
                        )
                    response_list:list = list(json.loads(response.text)['Children'])

                tmp_set:set
                response_list:list = [{"ID":tmp_set["Id"], "Name":tmp_set["Name"]}
                                      for tmp_set in response_list]

                file_set:set
                for file_set in response_list:
                    filename_parts:list = [self.sweep_name, dir_name, file_set["Name"]]
                    if "_".join(filename_parts) in self.files:
                        continue
                    #if "_".join(filename_parts) not in track_list:
                    #    self.track_files("_".join(filename_parts))
                    uri_parts:list = [
                        f'https://#REMOVED#.sf-api.com/sf/v3/Items({file_set["ID"]})',
                        '/Download'
                    ]
                    uri_path = "".join(uri_parts)
                    if not new_token:
                        token:str = self.token["access_token"]
                    else:
                        token:str = new_token
                    with requests.get(
                        uri_path,
                        stream=True,
                        headers={'Authorization' : f'Bearer {token}'},
                        allow_redirects=True
                        ) as response:
                        filename = os.path.join(self.destination, "_".join(filename_parts))
                        with open(filename, 'wb') as target:
                            shutil.copyfileobj(response.raw, target)
                        if "_".join(filename_parts) not in track_list:
                            self.track_files("_".join(filename_parts))
