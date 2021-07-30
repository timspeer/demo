'''core methods for reconcile'''
import os
import sys
import sqlite3
import configparser
import sqlalchemy
import fnmatch
from datetime import datetime
import subprocess
import typing
import traceback # pylint: disable=unused-import

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', "Globals")))
from send_email import send_email
from pdf_to_text import pdf_to_text # pylint: disable=unused-import

class Reconcile():
    '''
    reconcile generator
    facility => name of the CLIENT_Facility we are getting data from
    bypass => true will email errors and continue script
    test => true will ignore tracking databases
    '''
    def __init__(self, facility : str, bypass : bool=False, test : bool=False):
        self.facility:str = facility
        self.test:bool = test
        self.bypass:bool = bypass

        self.client, self.common = self.config()
        self.meta:object = sqlalchemy.MetaData()
        self.engine:object = sqlalchemy.create_engine(
            f'mssql+pymssql:{self.common["sql"]}',
            isolation_level="READ UNCOMMITTED"
            )
        self.smi_encounter:object = sqlalchemy.Table(
            'Encounter',
            self.meta,
            autoload=True,
            autoload_with=self.engine,
            schema="#REMOVED#.dbo"
            )
        self.smi_reconcile:object = sqlalchemy.Table(
            'Reconcile',
            self.meta,
            autoload=True,
            autoload_with=self.engine,
            schema="#REMOVED#.dbo"
            )
        self.root:os.PathLike = os.path.join(self.common['server'], self.client['root'])
        self.send_email:typing.Callable = send_email
        self.database:os.PathLike = os.path.join(
            os.path.join(sys.argv[0], '..'),
            f'{self.client["client"]}_{self.client["location"]}_reconcile.db'
        ).lower()

    def config(self) -> typing.Tuple[dict, dict]:
        '''returns two configuration dictionaries based on config.dale'''
        config_file:str = os.path.join(os.path.dirname(__file__), 'config.dale')
        config:object = configparser.ConfigParser()
        config.read(config_file)
        client:dict = dict(config.items(self.facility))
        common:dict = dict(config.items("COMMON"))
        return client, common

    def check(self, filepath:str, table:str=None, database:str=None) -> list:
        '''returns a list of files that aren't in the db'''
        if not database:
            database:os.PathLike = os.path.join(os.path.dirname(__file__), "reconcile.db")
        if not table:
            table:str = self.client["client"]+"_"+self.client["location"]
        connection:object = sqlite3.connect(database)
        connection.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT)')
        check:set = connection.execute(f"SELECT Filename FROM {table}").fetchall()
        check:list = ["".join(item).replace("''", "'") for item in check]
        if self.test:
            check:list = list()
        file_list:list = [os.path.join(filepath, item) for item in os.listdir(filepath)
                          if item not in check]
        file_list:list = [item for item in file_list
                          if not os.path.isdir(item) and not fnmatch.fnmatch(item, "*.log")]
        connection.close()
        return file_list

    def track_files(self, name:str, table:str=None, database:str=None, basename:bool=True) -> None:
        '''track files in db make sure to use os.path.basename()'''
        if basename:
            name:str = os.path.basename(name)
        if self.test:
            return
        name:str = name.replace("'", "''")
        date:datetime = datetime.now().strftime("%Y-%m-%d")
        if not database:
            database:os.PathLike = os.path.join(os.path.dirname(__file__), "reconcile.db")
        if not table:
            table:str = self.client["client"]+"_"+self.client["location"]
        connection:object = sqlite3.connect(database)
        connection.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT)')
        file_check:set = connection.execute(\
            f"SELECT Filename FROM {table} WHERE Filename = '{name}'").fetchone()
        if file_check:
            connection.close()
            return
        connection.execute(f'INSERT INTO {table} VALUES (?,?)', (name, date))
        connection.commit()
        connection.close()

    def load_reconcile_on_csn(self, dictionary:dict, table_object_default:object=None,
                              delete:list=None, specifics:dict=None) -> None:
        '''load database on csn'''
        def update(dict_:dict):
            with self.engine.connect() as conn:
                conn.execute(table_object.update(None)                      \
                    .where(sqlalchemy.and_(                                 \
                        table_object.c.CSN==dictionary["CSN"],              \
                        table_object.c.Location==dictionary["Location"],    \
                        table_object.c.Client==dictionary["Client"]))       \
                    .values(dict_))
        if not table_object_default:
            table_object:object = self.smi_reconcile
        else:
            table_object:object = table_object_default
        with self.engine.connect() as conn:
            query:set = conn.execute(table_object.select(None)          \
                .where(sqlalchemy.and_(                                 \
                    table_object.c.CSN==dictionary["CSN"],              \
                    table_object.c.Location==dictionary["Location"],    \
                    table_object.c.Client==dictionary["Client"]))
                ).fetchall()
        if query:
            if delete:
                for key in delete:
                    del dictionary[key]
            if specifics:
                update(specifics)
            else:
                update(dictionary)
        else:
            with self.engine.connect() as conn:
                conn.execute(table_object.insert(dictionary))

    def load_reconcile(self, dictionary:dict, table_object_default:object=None,
                       delete:list=None, specifics:dict=None) -> None:
        '''load #REMOVED#.dbo.Reconcile with data'''
        if not table_object_default:
            table_object:object = self.smi_reconcile
        else:
            table_object:object = table_object_default
        if not dictionary["MRN"]:
            with self.engine.connect() as conn:
                query:set = conn.execute(table_object.select(None)          \
                    .where(sqlalchemy.and_(                                 \
                        table_object.c.LName==dictionary["LName"],          \
                        table_object.c.FName==dictionary["FName"],          \
                        table_object.c.DOS==dictionary["DOS"],              \
                        table_object.c.Location==dictionary["Location"],    \
                        table_object.c.Client==dictionary["Client"]))
                    ).fetchall()
        else:
            with self.engine.connect() as conn:
                query:set = conn.execute(table_object.select(None)          \
                    .where(sqlalchemy.and_(                                 \
                        table_object.c.MRN==dictionary["MRN"],              \
                        table_object.c.DOS==dictionary["DOS"],              \
                        table_object.c.Location==dictionary["Location"],    \
                        table_object.c.Client==dictionary["Client"]))
                    ).fetchall()
        if query:
            if delete:
                for key in delete:
                    del dictionary[key]
            if specifics:
                with self.engine.connect() as conn:
                    conn.execute(table_object.update(None)\
                        .where(sqlalchemy.and_(\
                            table_object.c.MRN==dictionary["MRN"],\
                            table_object.c.DOS==dictionary["DOS"],\
                            table_object.c.Client==dictionary["Client"]))\
                        .values(specifics))
            else:
                if not dictionary["MRN"]:
                    with self.engine.connect() as conn:
                        conn.execute(table_object.update(None)\
                            .where(sqlalchemy.and_(\
                                table_object.c.LName==dictionary["LName"],\
                                    table_object.c.FName==dictionary["FName"],\
                                table_object.c.DOS==dictionary["DOS"],\
                                table_object.c.Client==dictionary["Client"]))\
                            .values(dictionary))
                else:
                    with self.engine.connect() as conn:
                        conn.execute(table_object.update(None)\
                            .where(sqlalchemy.and_(\
                                table_object.c.MRN==dictionary["MRN"],\
                                table_object.c.DOS==dictionary["DOS"],\
                                table_object.c.Client==dictionary["Client"]))\
                            .values(dictionary))
        else:
            with self.engine.connect() as conn:
                conn.execute(table_object.insert(dictionary))

    def check_in_phi_on_mrn(self, location:str=None):
        '''runs stored procedure - SCRIPT_SET_InPHI_PHIIncidentID_ON_MRN_DOS'''
        if not location:
            location:str = self.client['location']
        statement = [
            "USE #REMOVED# EXEC SCRIPT_SET_InPHI_PHIIncidentID_ON_MRN_DOS",
            "@client=:client, @location=:location"
        ]
        with self.engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(" ".join(statement)),
                client=self.client['client'],
                location=location
                )

    def check_encounter(self):
        '''runs stored procedure - SCRIPT_UPDATE_Reconcile_FROM_Encounter'''
        statement = [
            "EXEC #REMOVED#.dbo.SCRIPT_UPDATE_Reconcile_FROM_Encounter",
            "@client=:client, @location=:location"
        ]
        with self.engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(" ".join(statement)),
                client=self.client['client'],
                location=self.client['location']
                )

    @staticmethod
    def pdf_to_text(pdf:str, output_format:str) -> str:
        '''uses pdftotext to convert pdf to text'''
        result:str = subprocess.check_output([
            "pdftotext",
            f"-{output_format}",
            pdf,
            '-']
            ).decode("iso-8859-1")
        return result
