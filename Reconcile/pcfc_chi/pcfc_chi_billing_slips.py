'''PCFC CHI Billing Slips'''
import os
import sys
from fnmatch import fnmatch
from datetime import datetime
import pandas
import numpy
from dateutil.relativedelta import relativedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import methods

def main(facility:str) -> None:
    '''checks billing slips'''
    print("Billing Slips")
    reconcile:object = methods.Reconcile(facility, bypass=True)

    date:str = datetime.now().strftime("%Y.%m.%d")
    yesterday:str = (datetime.now()+relativedelta(days=-1)).strftime("%Y.%m.%d")

    check_list:list = reconcile.check(
        os.path.join(reconcile.root, reconcile.client["billing_slips"])
        )
    item:os.PathLike
    check_list:list = [
        item for item in check_list if (
            not fnmatch(item, f"*{date}*")
            and not fnmatch(item, f"*{yesterday}*")
            and fnmatch(item, "*.xlsx")
            )
        ]

    for excel in check_list:
        print(excel)
        try:
            dframe:object = pandas.read_excel(
                excel, sheet_name='Sheet1', dtype=str, header=0, usecols=(0,1,2,3,4)
                )
            dframe:object = dframe.replace(numpy.nan, '', regex=True)
            d_list:list = dframe.to_dict("records")
            item:dict
            for item in d_list:
                dict_:dict = {
                    "Client" : reconcile.client["client"],
                    "Location" : reconcile.client["location"],
                    "DOS" : item["Date of Service"],
                    "MRN" : item["Medical Record Number"],
                    "LName" : item["Last Name"],
                    "FName" : item["First Name"],
                    "Facility" : item["Facility"],
                    "BillingSlip" : excel
                }
                reconcile.load_reconcile(dict_)
            reconcile.track_files(excel)
        except Exception as exception:
            if reconcile.bypass:
                methods.send_email(methods.traceback.format_exc(), __doc__)
                continue
            print(excel)
            raise exception

if __name__ == "__main__":
    main("PCFC_CHI")
