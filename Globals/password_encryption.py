'''salt and pepper password and unsalt'''
from cryptography.fernet import Fernet
import sqlalchemy

PEPPER:str = '#REMOVED#'

def insert_password(username:str, password:str, description:str):
    '''insert password into database'''
    encrypted_password, salt = encrypt(password)
    meta:object = sqlalchemy.MetaData()
    engine:object = sqlalchemy.create_engine(
        '#REMOVED#', isolation_level='READ UNCOMMITTED')
    conn:object = engine.connect()
    smi_password:object = sqlalchemy.Table(
        'SMI_Passwords', meta, autoload=True, autoload_with=engine)

    statement:list = [
        "SELECT * FROM #REMOVED#",
        "WHERE Username = :username AND Description = :description"
    ]
    cleaned:str = sqlalchemy.text(" ".join(statement)) #Sanitizes
    query = conn.execute(
        cleaned,
        username=username,
        description=description
        ).fetchall()

    if query:
        update_statement:list = [
            "UPDATE #REMOVED#",
            "SET Password = :password, Salt = :salt",
            "WHERE Username = :username AND Description = :description"
        ]
        clean_update:str = sqlalchemy.text(" ".join(update_statement))
        conn.execute(
            clean_update,
            password=encrypted_password,
            salt=salt,
            username=username,
            description=description
            )
    else:
        insert_dict:dict = {
            "Username" : username,
            "Password" : encrypted_password,
            "Salt" : salt,
            "Description" : description
        }
        conn.execute(smi_password.insert(insert_dict))

def get_password(username:str, description:str):
    '''get password from db and decrypt it'''
    engine:object = sqlalchemy.create_engine(
        '#REMOVED#', isolation_level='READ UNCOMMITTED')
    conn:object = engine.connect()

    statement:list = [
        "SELECT Password, Salt FROM #REMOVED#",
        "WHERE Username = :username AND Description = :description"
    ]
    cleaned:object = sqlalchemy.text(" ".join(statement)) #Sanitize
    query:list = conn.execute(cleaned, username=username, description=description).fetchone()
    encrypted_password, salt = query[0].encode("UTF-8"), query[1].encode("UTF-8")
    password:str = decrypt(encrypted_password, salt)
    return password

def encrypt(password:str) -> bytes:
    '''encrypt, salt, pepper password'''
    peppered_password:bytes = (password+PEPPER).encode("UTF-8")

    salt:bytes = Fernet.generate_key()
    fernet_process:object = Fernet(salt)

    encrypted_password = fernet_process.encrypt(peppered_password)

    return encrypted_password, salt

def decrypt(encrypted_password:bytes, salt:bytes) -> str:
    '''decrypt password'''
    fernet_process:object = Fernet(salt)
    decrypted_password:bytes = fernet_process.decrypt(encrypted_password)
    decrypted_password:str = decrypted_password.decode("UTF-8").replace(PEPPER, '')

    return decrypted_password

