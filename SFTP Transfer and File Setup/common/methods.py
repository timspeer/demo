'''check and track in db'''
from datetime import datetime
import os
import sys
import sqlite3
import stat
import subprocess
import configparser
import paramiko
from dataclasses import dataclass
import fnmatch
import sqlalchemy
import traceback # pylint: disable=unused-import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', "Globals")))
from send_email import send_email # pylint: disable=unused-import
from password_encryption import get_password
from plan_id import plan_id # pylint: disable=unused-import
from psexec import psexec # pylint: disable=unused-import
from pdf_to_text import pdf_to_text # pylint: disable=unused-import

def custom_check(table : str, db : str, db_structure : str="(Filename TEXT, Date TEXT)"):
    '''check in db'''
    conn = sqlite3.connect(db)
    conn.execute(f'CREATE TABLE IF NOT EXISTS {table} {db_structure}')
    check = conn.execute(f"SELECT Filename FROM {table}").fetchall()
    check = ["".join(item) for item in check]
    conn.close()
    return check

def custom_track(name : str, table : str, db : str, db_structure : str="(Filename TEXT, Date TEXT)"):
    '''track files in db'''
    date = datetime.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db)
    conn.execute(f'CREATE TABLE IF NOT EXISTS {table} {db_structure}')
    conn.execute(f'INSERT INTO {table} VALUES (?,?)', (name, date))
    conn.commit()
    conn.close()

def check(table : str, filepath : str, db : str=r'#REMOVED#', test : bool=False, sftp : object=False, day : bool=False):
    '''check in db'''
    if not sftp:
        file_list = os.listdir(filepath)
    else:
        file_list = sftp.listdir_attr(filepath)
    conn = sqlite3.connect(db)
    if day:
        conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT, Day TEXT)')
    else:
        conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT)')
    check = conn.execute(f"SELECT Filename FROM {table}").fetchall()
    check = ["".join(item) for item in check]
    if test:
        check = []
    if not sftp:
        file_list = [os.path.join(filepath, item) for item in file_list if item not in check]
        file_list = [item for item in file_list if not os.path.isdir(item) and not fnmatch.fnmatch(item, "*.log")]
    else:
        file_list = [item for item in file_list if not stat.S_ISDIR(item.st_mode)]
        file_list = [(os.path.join(filepath, item.filename), item.st_mtime) for item in file_list if item.filename not in check]
    conn.close()
    return file_list

def track_files(name : str, table : str, db : str=r'#REMOVED#', day : bool=False, test : bool=False):
    '''track files in db'''
    if test:
        return
    date = datetime.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db)
    if day:
        conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT, Day TEXT)')
        conn.execute(f'INSERT INTO {table} VALUES (?,?,?)', (name, date, datetime.now().weekday()))
    else:
        conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT)')
        conn.execute(f'INSERT INTO {table} VALUES (?,?)', (name, date))
    conn.commit()
    conn.close()

def transfer(common : dict, client : dict, table : str=None, test : bool=False, day : bool=True):
    '''transfer setup'''
    if not table:
        table = client['sftp_table']
    conn = sqlite3.connect(common['sftp_db'])

    password:str = get_password(common['username'], "SMI SFTP")

    transport = paramiko.Transport((common['host'], int(common['port'])))
    transport.connect(username=common['username'], password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    check_list = check(table, client['sftp_dir'], sftp=sftp, day=day, test=test)

    return check_list, sftp, conn, transport

def standard_transfer(common : dict, client : dict, args : list = [], filepath : str='', test : bool=False):
    '''runs the file'''
    
    check_list, sftp, conn, transport = transfer(common, client, test=test)

    if filepath:
        local_dir = filepath
    else:
        local_dir = client['local_dir']

    if args:
        for arg in args:
            check_list = [item for item in check_list if not fnmatch.fnmatch(item[0], f"*{arg}*")]

    for file in check_list:
        name = os.path.basename(file[0])
        mod_time = file[1]
        sftp.get(os.path.join(client['sftp_dir'], name), os.path.join(local_dir, name))
        os.utime(os.path.join(local_dir, name), (mod_time, mod_time))
        print(os.path.join(client['sftp_dir'], name))
        track_files(name, client['sftp_table'], day=True)
   
    conn.close()
    sftp.close()
    transport.close()
    
def sql_upload(client : str, encounter : bool=True):
    '''fires the program'''
    meta = sqlalchemy.MetaData()
    engine = sqlalchemy.create_engine('mssql+pymssql://#REMOVED#/#REMOVED#')
    conn = engine.connect()
    truncate = [
        "SELECT col.name, col.max_length FROM #REMOVED#.sys.all_columns as col",
        "WITH (NOLOCK)",
        "INNER JOIN #REMOVED#.sys.all_objects as obj",
        "ON obj.object_id = col.object_id",
        "INNER JOIN #REMOVED#.sys.types as typ",
        "ON col.system_type_id = typ.system_type_id",
        "WHERE obj.name = 'SMI_Person' AND typ.name in ('char', 'varchar')"
    ]
    query = conn.execute(" ".join(truncate))
    truncate = dict(query.fetchall())
    smi_person_table = sqlalchemy.Table('SMI_Person', meta, autoload=True, autoload_with=engine)
    def trunc(dictionary : dict):
        for key, val in truncate.items():
            try:
                replace_dict = {"'" : "''", "|" : "", "^" : " "}
                for rkey, rval in replace_dict.items():
                    dictionary[key] = str(dictionary[key]).strip().replace(rkey, rval)
                dictionary[key] = dictionary[key][:val]
            except (KeyError, TypeError):
                pass
    def to_sql(dictionary : dict, loc : str=''):
        loc_name = ''
        if loc:
            loc_name = f"AND LOC_NAME like '%{loc}%'"
        if encounter:
            csn = dictionary["encounterID"]
        mrn = dictionary["PH_MRN"]
        dos = dictionary['AN_DATE']
        if encounter:
            statement = [
                "SELECT PH_MRN FROM [#REMOVED#].[dbo].[SMI_Person]",
                "WITH (NOLOCK)",
                f"WHERE client = '{client}' AND encounterID = '{csn}'",
                loc_name
            ]
            if loc:
                statement.append(f"AND LOC_NAME like '%{loc}%'")
        else:
            statement = [
                "SELECT PH_MRN FROM [#REMOVED#].[dbo].[SMI_Person]",
                "WITH (NOLOCK)",
                f"WHERE client = '{client}' AND PH_MRN = '{mrn}' AND AN_DATE = '{dos}'",
                loc_name
            ]
        query = conn.execute(" ".join(statement)).fetchall()
        if query:
            statement = []
            for key, val in dictionary.items():
                skip_list = [
                    "recordLoadedDT", 
                    "csrDT",
                    "importFileCreated",
                    "recordHeld",
                    "recordCoded",
                    'checkedOut'
                ]
                if key in skip_list:
                    continue
                statement.append(f"{key} = '{val}'")
            statement = ", ".join(statement)
            if encounter:
                update_statement = [
                    f"UPDATE #REMOVED#.dbo.SMI_Person WITH (ROWLOCK) SET {statement}",
                    f"WHERE client = '{client}' AND encounterID = '{csn}'",
                    loc_name
                ]
            else:
                update_statement = [
                    f"UPDATE #REMOVED#.dbo.SMI_Person WITH (ROWLOCK) SET {statement}",
                    f"WHERE client = '{client}' AND PH_MRN = '{mrn}' AND AN_DATE = '{dos}'",
                    loc_name
                ]
            conn.execute(" ".join(update_statement))
        else:
            conn.execute(smi_person_table.insert(dictionary))
    return to_sql, trunc, conn, meta, sqlalchemy, engine

def sql_encounter():
    '''new db methods'''
    meta = sqlalchemy.MetaData()
    engine = sqlalchemy.create_engine(f'mssql+pymssql://#REMOVED#/#REMOVED#', isolation_level='READ UNCOMMITTED')
    conn = engine.connect()
    smi_encounter = sqlalchemy.Table('#REMOVED#', meta, autoload=True, autoload_with=engine)
    smi_insurance = sqlalchemy.Table('#REMOVED#', meta, autoload=True, autoload_with=engine)
    smi_providers = sqlalchemy.Table('#REMOVED#', meta, autoload=True, autoload_with=engine)
    smi_codes = sqlalchemy.Table('#REMOVED#', meta, autoload=True, autoload_with=engine)

    def load_database(csn : str, table : str, table_object : object, original_dictionary : dict):
        dictionary = original_dictionary.copy()
        if table_object != smi_encounter:
            statement = [
                f"SELECT * FROM #REMOVED#.dbo.{table}",
                "WHERE CSN = :csn AND Rank = :rank"
            ]
            if table_object == smi_providers:
                name = dictionary['RawNameProvider']
                type_ = dictionary["TypeProvider"]
                s_ = [
                    f"AND RawNameProvider = '{name}'",
                    f"AND TypeProvider = '{type_}'"
                ]
                statement.extend(s_)
            elif table_object == smi_codes:
                type_ = dictionary['Type']
                statement.append(f"AND Type = '{type_}'")
            query_text = sqlalchemy.text(" ".join(statement))
            query = conn.execute(query_text, table=table, csn=csn, rank=dictionary["Rank"]).fetchall()
            if query:
                del dictionary["CSN"]
                if table_object == smi_providers:
                    id_ = conn.execute(table_object.update()\
                        .where(sqlalchemy.and_(\
                            table_object.c.CSN==csn,\
                            table_object.c.Rank==dictionary["Rank"],\
                            table_object.c.RawNameProvider==dictionary["RawNameProvider"],
                            table_object.c.TypeProvider==dictionary["TypeProvider"]))\
                        .values(dictionary)\
                        .returning(table_object.c.ID.label('ID')))
                    id_ = id_.fetchone()[0]
                elif table_object == smi_codes:
                    id_ = conn.execute(table_object.update()\
                        .where(sqlalchemy.and_(\
                            table_object.c.CSN==csn,\
                            table_object.c.Rank==dictionary["Rank"],\
                            table_object.c.Type==dictionary["Type"]))\
                        .values(dictionary)\
                        .returning(table_object.c.ID.label('ID')))
                    id_ = id_.fetchone()[0]
                else:
                    id_ = conn.execute(table_object.update()\
                        .where(sqlalchemy.and_(\
                            table_object.c.CSN==csn,\
                            table_object.c.Rank==dictionary["Rank"]))\
                        .values(dictionary)\
                        .returning(table_object.c.ID.label('ID')))
                    id_ = id_.fetchone()[0]
                return id_
            else:
                id_ = conn.execute(table_object.insert(dictionary).returning(table_object.c.ID.label('ID')))
                id_ = id_.fetchone()[0]
                if table_object == smi_providers:
                    try:
                        _ = dictionary["NPI"]
                        statement = [
                            "UPDATE #REMOVED#.dbo.#REMOVED#",
                            "SET LNameProvider = prov.LName, FNameProvider = prov.FName",
                            "FROM #REMOVED#.dbo.#REMOVED# as smi",
                            "INNER JOIN SMI_Crosswalk.dbo.Providers as prov",
                            "ON smi.Client = prov.Client AND smi.NPIProvider = prov.NPI",
                            "WHERE smi.ID = :id"
                        ]
                    except KeyError:
                        statement = [
                            "UPDATE #REMOVED#.dbo.#REMOVED#",
                            "SET LNameProvider = prov.LName, FNameProvider = prov.FName, NPIProvider = prov.NPI",
                            "FROM #REMOVED#.dbo.#REMOVED# as smi",
                            "INNER JOIN SMI_Crosswalk.dbo.Providers as prov",
                            "ON smi.Client = prov.Client AND smi.RawNameProvider = prov.RawName",
                            "WHERE smi.ID = :id"
                        ]
                    conn.execute(sqlalchemy.text(" ".join(statement)), id=id_)
                return id_
        else:
            statement = [
                f"SELECT * FROM #REMOVED#.dbo.{table}",
                "WHERE CSN = :csn"
            ]
            query_text = sqlalchemy.text(" ".join(statement))
            query = conn.execute(query_text, table=table, csn=csn).fetchall()
            if query:
                del dictionary["CSN"]
                id_ = conn.execute(table_object.update()\
                    .where(table_object.c.CSN==csn)\
                    .values(dictionary)\
                    .returning(table_object.c.ID.label('ID')))
                id_ = id_.fetchone()[0]
                return id_
            else:
                id_ = conn.execute(table_object.insert(dictionary).returning(table_object.c.ID.label('ID')))
                id_ = id_.fetchone()[0]
                return id_
    return smi_encounter, smi_insurance, smi_providers, smi_codes, load_database, conn

def config(facility:str):
    '''settings'''
    config_file:os.PathLike = os.path.join(os.path.dirname(__file__), 'config.dale')
    configuration:object = configparser.ConfigParser()
    configuration.read(config_file)
    client:dict = dict(configuration.items(facility))
    common:dict = dict(configuration.items("COMMON"))

    return client, common

class Transfer():
    '''create connection with sftp server'''
    def __init__(self, facility:str, database:os.PathLike=None, table:str="SFTP"):
        self.client, common = config(facility)
        self.table:str = table

        if not database:
            self.database:os.PathLike = os.path.join(
                os.path.dirname(sys.argv[0]),
                self.client["database"]
                )
        else:
            self.database:os.PathLike = database

        password:str = get_password(common['username'], "SMI SFTP")
        self.transport:object = paramiko.Transport((common['host'], int(common['port'])))
        self.transport.connect(username=common['username'], password=password)
        self.sftp:object = paramiko.SFTPClient.from_transport(self.transport)
        self.root:os.PathLike = os.path.join(common['server'], self.client['root'])

    def check(self, filepath:str=None) -> list:
        '''check for files on sftp server'''
        if not filepath:
            filepath:os.PathLike = self.client["sftp_dir"]
        file_list:list = self.sftp.listdir_attr(filepath)
        conn:object = sqlite3.connect(self.database)
        conn.execute(
            f'CREATE TABLE IF NOT EXISTS {self.table} (Filename TEXT, Date TEXT, Day TEXT)'
            )
        check_db:set = conn.execute(f"SELECT Filename FROM {self.table}").fetchall()
        check_db:list = ["".join(item).replace("''", "'") for item in check_db]
        file_list:list = [item for item in file_list if not stat.S_ISDIR(item.st_mode)]
        file_list:list = [(os.path.join(filepath, item.filename), item.st_mtime)
                          for item in file_list if item.filename not in check_db]
        conn.close()
        return sorted(file_list, reverse=True)

    def track_files(self, filename:str, basename:bool=True):
        '''track files in db'''
        date:str = datetime.today().strftime("%Y-%m-%d")
        weekday:int = datetime.now().weekday()
        if basename:
            filename:str = os.path.basename(filename)
        filename:str = filename.replace("''", "'")
        conn:object = sqlite3.connect(self.database, timeout=10)
        conn.execute(
            f'CREATE TABLE IF NOT EXISTS {self.table} (Filename TEXT, Date TEXT, Day TEXT)'
            )
        conn.execute(
            f'INSERT INTO {self.table} VALUES (?,?,?)', (filename, date, weekday)
            )
        conn.commit()
        conn.close()

class FileProcess():
    '''
    facility ==> the name of the client plus facility from the config.dale file
    bypass ==> this is used to report an error then continue without breaking
    test ==> this will cause the script to ignore the filetracking database
    day ==> this will cause the tracking function to include the day \
        (I have an idea  for machine learning with it)
    '''
    def __init__(self, facility : str, bypass : bool=False, test : bool=False, day : bool=False, sftp:bool=True):
        self.facility = facility
        self.client, self.common = config(facility)
        self.test = test
        self.bypass = bypass
        self.date = datetime.today().strftime("%Y-%m-%d")
        if sftp:
            self.sftp, self.transport = self.transfer()
        self.day = day
        self.meta, self.engine = self.sql_encounter()
        self.smi_encounter = sqlalchemy.Table(
            '#REMOVED#',
            self.meta,
            autoload=True,
            autoload_with=self.engine
            )
        self.smi_insurance = sqlalchemy.Table(
            '#REMOVED#',
            self.meta,
            autoload=True,
            autoload_with=self.engine
            )
        self.smi_providers = sqlalchemy.Table(
            '#REMOVED#',
            self.meta,
            autoload=True,
            autoload_with=self.engine
            )
        self.smi_codes = sqlalchemy.Table(
            '#REMOVED#',
            self.meta,
            autoload=True,
            autoload_with=self.engine
            )
        self.reconcile = os.path.join(
            self.common['server'],
            self.common['reconcile'],
            self.client['reconcile']
            )
        self.root = os.path.join(self.common['server'], self.client['root'])
        self.incoming_charge = os.path.join(self.common['server'], self.common['incoming_charges'])

    def transfer(self):
        '''transfer setup'''
        password:str = get_password(self.common['username'], "SMI SFTP")
        transport = paramiko.Transport((self.common['host'], int(self.common['port'])))
        transport.connect(username=self.common['username'], password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        return sftp, transport

    def check(
        self,
        table : str,
        filepath : str,
        sftp : object=False,
        reverse : bool=True,
        database : str=None
        ):
        '''
        check in db
        table ==> name of table used to track
        filepath ==> searches through this directory for files no in the db
        sftp ==> for searching in an sftp server
        reverse ==> traverse the directory forward or backwards
        database ==> database to use, the default is filetracker.db
        '''
        if not database:
            database = os.path.join(os.path.dirname(__file__), 'filetracker.db')
        if not sftp:
            file_list = os.listdir(filepath)
        else:
            file_list = sftp.listdir_attr(filepath)
        conn = sqlite3.connect(database)
        if self.day:
            conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT, Day TEXT)')
        else:
            conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT)')
        check_db = conn.execute(f"SELECT Filename FROM {table}").fetchall()
        check_db = ["".join(item).replace("''", "'") for item in check_db]
        if self.test:
            check_db = []
        if not sftp:
            file_list = [os.path.join(filepath, item) for item in file_list if item not in check_db]
            file_list = [
                    item for item in file_list
                    if not os.path.isdir(item)
                    and not fnmatch.fnmatch(item, "*.log")
                    and not fnmatch.fnmatch(item, "*Thumbs.db")
                ]
        else:
            file_list = [item for item in file_list if not stat.S_ISDIR(item.st_mode)]
            file_list = [
                (os.path.join(filepath, item.filename), item.st_mtime) for item in file_list\
                    if item.filename not in check_db
                ]
        conn.close()
        return sorted(file_list, reverse=reverse)

    def track_files(self, name : str, table : str, basename : bool=True, database:None = None):
        '''track files in db'''
        if basename:
            name = os.path.basename(name)
        if self.test:
            return
        name:str = name.replace("''", "'")
        if not database:
            database = os.path.join(os.path.dirname(__file__), 'filetracker.db')
        conn = sqlite3.connect(database, timeout=10)
        if self.day:
            conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT, Day TEXT)')
            conn.execute(f'INSERT INTO {table} VALUES (?,?,?)',\
                (name, self.date, datetime.now().weekday()))
        else:
            conn.execute(f'CREATE TABLE IF NOT EXISTS {table} (Filename TEXT, Date TEXT)')
            conn.execute(f'INSERT INTO {table} VALUES (?,?)', (name, self.date))
        conn.commit()
        conn.close()
    
    def load_database(self, csn : str, table : str, table_object : object, original_dictionary : dict):
        '''load database'''
        dictionary = original_dictionary.copy()
        with self.engine.connect() as conn:
            if table_object != self.smi_encounter:
                statement = [
                    f"SELECT * FROM #REMOVED#.dbo.{table}",
                    "WHERE CSN = :csn AND Rank = :rank"
                ]
                if table_object == self.smi_providers:
                    name = dictionary['RawNameProvider'].replace("'", "''")
                    type_ = dictionary["TypeProvider"]
                    s_ = [
                        f"AND RawNameProvider = '{name}'",
                        f"AND TypeProvider = '{type_}'"
                    ]
                    statement.extend(s_)
                elif table_object == self.smi_codes:
                    type_ = dictionary['Type']
                    statement.append(f"AND Type = '{type_}'")
                query_text = sqlalchemy.text(" ".join(statement))
                query = conn.execute(query_text, table=table, csn=csn, rank=dictionary["Rank"]).fetchall()
                if query:
                    del dictionary["CSN"]
                    if table_object == self.smi_providers:
                        id_ = conn.execute(table_object.update()\
                            .where(sqlalchemy.and_(\
                                table_object.c.CSN==csn,\
                                table_object.c.Rank==dictionary["Rank"],\
                                table_object.c.RawNameProvider==dictionary["RawNameProvider"],
                                table_object.c.TypeProvider==dictionary["TypeProvider"]))\
                            .values(dictionary)\
                            .returning(table_object.c.ID.label('ID')))
                        id_ = id_.fetchone()[0]
                    elif table_object == self.smi_codes:
                        id_ = conn.execute(table_object.update()\
                            .where(sqlalchemy.and_(\
                                table_object.c.CSN==csn,\
                                table_object.c.Rank==dictionary["Rank"],\
                                table_object.c.Type==dictionary["Type"]))\
                            .values(dictionary)\
                            .returning(table_object.c.ID.label('ID')))
                        id_ = id_.fetchone()[0]
                    else:
                        id_ = conn.execute(table_object.update()\
                            .where(sqlalchemy.and_(\
                                table_object.c.CSN==csn,\
                                table_object.c.Rank==dictionary["Rank"]))\
                            .values(dictionary)\
                            .returning(table_object.c.ID.label('ID')))
                        id_ = id_.fetchone()[0]
                    return id_
                else:
                    id_ = conn.execute(table_object.insert(dictionary).returning(table_object.c.ID.label('ID')))
                    id_ = id_.fetchone()[0]
                    if table_object == self.smi_providers:
                        try:
                            _ = dictionary["NPI"]
                            statement = [
                                "UPDATE #REMOVED#.dbo.#REMOVED#",
                                "SET LNameProvider = prov.LName, FNameProvider = prov.FName",
                                "FROM #REMOVED#.dbo.#REMOVED# as smi",
                                "INNER JOIN SMI_Crosswalk.dbo.Providers as prov",
                                "ON smi.Client = prov.Client AND smi.NPIProvider = prov.NPI",
                                "WHERE smi.ID = :id"
                            ]
                        except KeyError:
                            statement = [
                                "UPDATE #REMOVED#.dbo.#REMOVED#",
                                "SET LNameProvider = prov.LName, FNameProvider = prov.FName, NPIProvider = prov.NPI",
                                "FROM #REMOVED#.dbo.#REMOVED# as smi",
                                "INNER JOIN SMI_Crosswalk.dbo.Providers as prov",
                                "ON smi.Client = prov.Client AND smi.RawNameProvider = prov.RawName",
                                "WHERE smi.ID = :id"
                            ]
                        conn.execute(sqlalchemy.text(" ".join(statement)), id=id_)
                    return id_
            else:
                statement = [
                    f"SELECT * FROM #REMOVED#.dbo.{table}",
                    "WHERE CSN = :csn"
                ]
                query_text = sqlalchemy.text(" ".join(statement))
                query = conn.execute(query_text, table=table, csn=csn).fetchall()
                if query:
                    del dictionary["CSN"]
                    try:
                        del dictionary["CSR"]
                    except KeyError:
                        pass
                    id_ = conn.execute(table_object.update()\
                        .where(table_object.c.CSN==csn)\
                        .values(dictionary)\
                        .returning(table_object.c.ID.label('ID')))
                    id_ = id_.fetchone()[0]
                    return id_
                id_ = conn.execute(table_object.insert(dictionary).returning(table_object.c.ID.label('ID')))
                id_ = id_.fetchone()[0]
                return id_
    
    def facility_crosswalk(self):
        '''runs stored procedure - SCRIPT_SET_Facility_ML_IN_#REMOVED#'''
        statement = [
            "EXEC SMI_Crosswalk.dbo.SCRIPT_SET_Facility_ML_IN_#REMOVED#",
            "@client=:client, @location=:location"
        ]
        with self.engine.begin() as conn:
            conn.execute(sqlalchemy.text(" ".join(statement)), client=self.client['client'], location=self.client['location'])

    def anestheisa_type_crosswalk(self):
        '''runs stored procedure - #REMOVED#_AnesthesiaType_ML'''
        with self.engine.connect() as conn:
            conn.execute("EXEC SMI_Crosswalk.dbo.#REMOVED#_AnesthesiaType_ML")

    def reconcile_smi_tools(self):
        '''run reconcile'''
        subprocess.call(["python", self.reconcile])

    @staticmethod
    def pdf_to_text(pdf : str, output_format : str) -> str:
        '''uses pdftotext to convert pdf to text'''
        result = subprocess.check_output([
            "pdftotext", #program name
            f"-{output_format}", #argument for output ie layout/table/simple/raw
            pdf, #pdf to read
            '-' #forces output to stdout otherwise it would go to file
            ]).decode("iso-8859-1") #needed to read some latin characters
        return result

    @staticmethod
    def query(statement : list):
        text = sqlalchemy.text(" ".join(statement))
        return text

    @staticmethod
    def sql_encounter():
        '''new db methods'''
        meta = sqlalchemy.MetaData()
        engine = sqlalchemy.create_engine('mssql+pymssql://#REMOVED#', isolation_level='READ UNCOMMITTED')

        return meta, engine
