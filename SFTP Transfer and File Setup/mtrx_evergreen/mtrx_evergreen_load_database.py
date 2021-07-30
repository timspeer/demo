'''load database from xml'''
import sys
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import traceback

import mtrx_evergreen_encounter
import mtrx_evergreen_providers
import mtrx_evergreen_codes
import mtrx_evergreen_generate_pdf

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')))
from common import methods

def main(facility):
    '''create dictionaries from xml'''

    fp_class = methods.FileProcess(facility, bypass=True, test=False)

    check_list = fp_class.check(fp_class.client['setup_table'], os.path.join(fp_class.root, "XML"))

    pdf_dir = os.path.join(fp_class.root, 'Anesthesia Records and Demographics PDFs')


    for file in check_list:
        try:
            print(file)
            tree = ET.parse(file)
            root = tree.getroot()
            csrdt = datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d")
            encounter_dict = mtrx_evergreen_encounter.main(csrdt, fp_class.client["client"], file, root)
            csn = encounter_dict["CSN"]
            encounter_dict["Filename"] = mtrx_evergreen_generate_pdf.main(root, pdf_dir, encounter_dict)
            id_ = fp_class.load_database(csn, "Encounter", fp_class.smi_encounter, encounter_dict)
            provider_list = mtrx_evergreen_providers.main(id_, csn, fp_class.client["client"], root)
            if provider_list:
                for provider in provider_list:
                    fp_class.load_database(csn, "SMI_Provider", fp_class.smi_providers, provider)
            code_list = mtrx_evergreen_codes.main(id_, csn, root)
            if code_list:
                for code in code_list:
                    fp_class.load_database(csn, "Codes", fp_class.smi_codes, code)
            fp_class.track_files(os.path.basename(file), fp_class.client['setup_table'])
            print(file)
        except Exception as exception:
            if fp_class.bypass:
                methods.send_email(file+"\n\n"+traceback.format_exc(), "MTRX Evergreen Load Database")
                continue
            else:
                print(file)
                raise exception
       
if __name__ == "__main__":
    main("MTRX_Evergreen")
        
