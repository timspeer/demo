'''MTRX Evergreen'''
import sys
import os

import mtrx_evergreen_load_database
import mtrx_evergreen_transfer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')))
from common import methods

def main():
    '''program trigger'''
    facility = 'MTRX_Evergreen'

    mtrx_evergreen_transfer.main(facility)
    mtrx_evergreen_load_database.main(facility)

    fp_class = methods.FileProcess(facility)

    fp_class.facility_crosswalk()

    fp_class.anestheisa_type_crosswalk()

    fp_class.reconcile_smi_tools()
    
if __name__ == "__main__":
    main()
