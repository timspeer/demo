'''common methods'''
import configparser
import os
import json
import requests
import sys
from fnmatch import fnmatch
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse
import sqlite3
import typing

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', "Globals")))
from send_email import send_email
from password_encryption import get_password

class Sharefile():
    '''Create Sharefile file transport class'''
    def __init__(self, client_name : str):
        self.client_name:str = client_name
        self.client:dict
        self.common:dict
        self.client, self.common = self.config()
        self.client_id:str = get_password("ClientID", "Sharefile API")
        self.client_secret:str = get_password("ClientSecret", "Sharefile API")
        self.password:str = get_password(self.common["username"], "Sharefile API")
        self.token:str = self.authenticate()
        self.doctors:list = self.get_doctors()
        self.year:str = datetime.now().strftime("%Y")
        self.month:str = datetime.now().strftime("%m")
        self.active_year:str = (datetime.now() + relativedelta(months=-1)).strftime("%Y")
        self.active_month:str = (datetime.now() + relativedelta(months=-1)).strftime("%m")
        self.reports:os.PathLike = os.path.join(
            self.common["reports"],
            self.client['client'],
            f"{self.active_year}.{self.active_month}"
            )
        self.send_email:typing.Callable = send_email

    def config(self) -> typing.Tuple[str, str]:
        '''setup and file transport'''
        config_file:os.PathLike = os.path.join(os.path.dirname( __file__ ) ,'config.dale')
        config:object = configparser.ConfigParser()
        config.read(config_file)
        client:dict = dict(config.items(self.client_name))
        common:dict = dict(config.items("COMMON"))
        return client, common

    def get_doctors(self, database:str=os.path.join(os.path.dirname(__file__), "test.db")) -> list:
        '''get list of doctors'''
        conn:object = sqlite3.connect(database)
        conn.execute(f'CREATE TABLE IF NOT EXISTS {self.client["table"]} (Doctor TEXT, Date TEXT)')
        check:list = conn.execute(f'SELECT Doctor FROM {self.client["table"]}').fetchall()
        check:list = ["".join(item) for item in check]
        conn.close()
        return check

    def authenticate(self) -> str:
        '''authenticate session'''
        token_url:str = urllib.parse.urljoin(self.common["url"], "/oauth/token")
        headers:dict = {'Content-Type' : 'application/x-www-form-urlencoded'}
        data:dict = {
            'grant_type' : 'password',
            'username' : self.common["username"],
            'password' : self.password,
            }
        response:object = requests.post(
            token_url,
            data=data,
            verify=True,
            auth=(self.client_id, self.client_secret),
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

    def check_folders(self) -> list:
        '''get list of folders'''
        uri_parts:list = [
            'https://#REMOVED#.sf-api.com/sf/v3/Items(allshared)/ByPath?path=/',
            self.client["root"],
            "&$expand=Children&$select=Children/Name"
        ]
        uri_path:str = "".join(uri_parts)
        response:object = requests.get(
            uri_path,
            headers={'Authorization' : f'Bearer {self.token["access_token"]}'}
            )

        response_list:list = list(json.loads(response.text)['Children'])

        return_list:list = [item['Name'] for item in response_list]

        return return_list

    def query_file(self, provider) -> list:
        '''get list of folders'''
        match = None
        uri_parts = [
            'https://#REMOVED#.sf-api.com/sf/v3/Items(allshared)/ByPath?path=/',
            self.client["root"],
            f'/{provider}/{self.active_year}/{self.active_year}.{self.active_month}',
            "&$expand=Children&$select=Children/Name"
        ]
        uri_path:str = "".join(uri_parts)
        response:object = requests.get(
            uri_path,
            headers={'Authorization' : f'Bearer {self.token["access_token"]}'}
            )
        if response.status_code == 404:
            return match
        response_list:list = list(json.loads(response.text)["Children"])
        file_list:list = [item['Name'] for item in response_list]

        for file in file_list:
            if fnmatch(file, f"* {provider}.pdf"):
                match = file

        return match
        
    def create_directories(self, providers) -> None:
        '''get root level item'''
        uri_parts:list = [
            'https://#REMOVED#.sf-api.com/sf/v3/Items(allshared)/ByPath?path=/',
            self.client["root"]
        ]
        uri_path:str = "".join(uri_parts)
        response:object = requests.get(
            uri_path,
            headers={'Authorization' : f'Bearer {self.token["access_token"]}'}
            )
        root_id:int = json.loads(response.text)["Id"]
        for doc in providers:
            id_:int = root_id
            folders:list = [doc, self.active_year, f"{self.active_year}.{self.active_month}"]
            for idx, folder in enumerate(folders):
                item:str = "/".join(folders[:idx+1])
                uri_parts:list = [
                    f'https://#REMOVED#.sf-api.com/sf/v3/Items({root_id})',
                    f'/ByPath?path=/{item}'
                ]
                uri_path:str = "".join(uri_parts)
                response:object = requests.get(
                    uri_path,
                    headers={'Authorization' : f'Bearer {self.token["access_token"]}'}
                    )
                if response.status_code == 200:
                    id_:int = json.loads(response.text)["Id"]
                elif response.status_code == 404:
                    if idx == 0:
                        return
                    uri_parts:list = [
                        f'https://#REMOVED#.sf-api.com/sf/v3/Items({id_})',
                        '/Folder?overwrite=false&passthrough=false'
                    ]
                    post_uri = "".join(uri_parts)
                    headers = {
                        'Authorization' : f'Bearer {self.token["access_token"]}',
                        "Content-Type" : "application/json"
                        }
                    response:object = requests.post(
                        post_uri,
                        data=json.dumps({"Name" : folder}),
                        headers=headers
                        )
                    id_:int = json.loads(response.text)["Id"]

    def upload_file(self, provider:str, filepath:str) -> str:
        '''format upload'''
        path_parts:list = [
            provider,
            self.active_year,
            f"{self.active_year}.{self.active_month}"
        ]
        sharefile_path = '/'.join(path_parts)

        uri_parts:list = [
            'https://#REMOVED#.sf-api.com/sf/v3/Items(allshared)/ByPath?path=/',
            f'{self.client["root"]}/{sharefile_path}'
        ]
        uri_path:str = "".join(uri_parts)
        response:object = requests.get(
            uri_path,
            headers={'Authorization' : f'Bearer {self.token["access_token"]}'}
            )

        id_:int = json.loads(response.text)["Id"]

        upload_uri:str = f'https://#REMOVED#.sf-api.com/sf/v3/Items({id_})/Upload?overwrite=false'
        upload_response:object = requests.get(
            upload_uri,
            headers={'Authorization' : f'Bearer {self.token["access_token"]}'}
            )

        chunk_uri:str = json.loads(upload_response.text)["ChunkUri"]

        upload_file:typing.Dict[str, typing.TextIO] = {"File1" : open(filepath, 'rb')}

        response:object = requests.post(chunk_uri, files=upload_file)

        return response.text
