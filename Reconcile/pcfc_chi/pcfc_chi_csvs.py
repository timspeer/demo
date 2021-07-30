'''PCFC CHI read csvs'''
import os
import sys
import traceback
from datetime import datetime
import pandas
import numpy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import methods

def main(facility) -> None:
    '''read csv'''
    print(__doc__)
    reconcile:object = methods.Reconcile(facility, bypass=False)

    database:os.PathLike = os.path.join(os.path.dirname(__file__), reconcile.client['database'])
    check_list:list = reconcile.check(
        os.path.join(reconcile.root, "Demographics TEXT"), database=database
        )

    for csv in check_list:
        print(csv)
        try:
            dframe:object = pandas.read_csv(csv, sep="|", dtype=str, encoding="ISO-8859-1")
            dframe:object = dframe.replace(numpy.nan, '', regex=True)
            d_list:list = dframe.to_dict('records')
            for dict_ in d_list:
                print(dict_)
                name:list = dict_["PATIENT NAME"].split(",")
                lname:str = name.pop(0)
                fname:str = name[0].split()[0]
                to_database:dict = {
                    "Client" : reconcile.client["client"],
                    "Location" : reconcile.client['location'],
                    "DOS" : datetime.strptime(dict_['SURGERY DATE (YYYYMMDD)'], "%Y%m%d"),
                    "MRN" : dict_['PATIENT MEDICAL RECORD NUMBER'],
                    "LName" : lname,
                    "FName" : fname,
                    "DOB" : datetime.strptime(dict_["PATIENT DOB"], "%m/%d/%Y"),
                    "Facility" : dict_["LOC_NAME"],
                    "Schedule" : csv,
                }
                update_dict:dict = {"Schedule" : csv,}
                reconcile.load_reconcile(to_database, specifics=update_dict)
            reconcile.track_files(csv, database=database)
        except Exception as exception:
            if reconcile.bypass:
                reconcile.send_email(csv+"\n\n"+traceback.format_exc(), __doc__)
                continue
            print(csv)
            raise exception

if __name__ == "__main__":
    main("PCFC_CHI")
