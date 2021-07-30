'''upload the file'''
import sys
import  os
from datetime import datetime
import requests
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', "Globals")))
from send_email import send_email
from password_encryption import get_password

def main():
    '''triggers the module'''
    date = datetime.now().strftime("%Y-%m-%d")
    year = datetime.now().year
    username = '#REMOVED#'
    password:str = get_password(username, "GVAA Survey Vitals API")
    source_file = fr'#REMOVED#'
    url = '#REMOVED#'
    files = {
        "profileKey" : (None, "#REMOVED#"),
        'pfile' : open(source_file, 'rb')
    }
    r = requests.post(
        url=url,
        auth=(username, password),
        verify=r'#REMOVED#',
        files=files
        )
    print(r.text)



if __name__ == "__main__":
    try:
        main()
    except Exception as exception:
        send_email(traceback.format_exc(), "GVAA Survey Vitals")
        raise exception
