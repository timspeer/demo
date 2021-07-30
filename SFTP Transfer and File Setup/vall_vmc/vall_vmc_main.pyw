'''VALL VMC Load Encounter'''
import sys
import os

import vall_vmc_transfer
import vall_vmc_load_database

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import methods

def main(facility:str, bypass:str=None) -> None:
    '''program trigger'''
    try:
        vall_vmc_transfer.main(facility, bypass)
        vall_vmc_load_database.main(facility, bypass)

        fp_class:object = methods.FileProcess(facility, sftp=False)

        fp_class.facility_crosswalk()

        fp_class.anestheisa_type_crosswalk()

        #fp_class.reconcile_smi_tools()

    except Exception as exception:
        if bypass:
            methods.send_email(methods.traceback.format_exc(), __doc__)
        raise exception

if __name__ == "__main__":
    fac:str = "VALL_VMC"
    if len(sys.argv) > 1:
        main(fac, "bypass")
    else:
        main(fac)
