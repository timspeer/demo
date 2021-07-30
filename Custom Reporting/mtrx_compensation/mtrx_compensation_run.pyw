'''load database from xml'''
import sys
import os
import xml.etree.ElementTree as ET
from datetime import datetime

import methods

def main():
    '''create dictionaries from xml'''

    process = methods.FileProcess("MTRX_Compensation", bypass=False, test=False)

    custom_reporting = process.sqlalchemy.Table('MTRX_Compensation', process.meta, autoload=True, autoload_with=process.engine)

    check_list = process.check(process.section['table'], os.path.join(process.root))

    conn = process.conn

    for file in check_list:
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            rounding_list:list = root.findall(".//*postop-rounding-encounter")
            if not rounding_list:
                process.track_files(file, process.section['table'])
                continue
            print(file)
            for rounding in rounding_list:
                sys_label = rounding.find(".//*section")
                if sys_label:
                    sys_label = sys_label.attrib["sys-label"]
                else:
                    sys_label = None
                encounter = datetime.fromisoformat(rounding.find("./encountered-at").text)
                provider_lname = rounding.find("./updater/user/last-name").text
                provider_fname = rounding.find("./updater/user/first-name").text
                npi = rounding.find("./updater/user/national-provider-id").text
                pat_lname = root.find("./case/case-info/patient/last-name").text
                pat_fname = root.find("./case/case-info/patient/first-name").text
                mrn = root.find("./case/case-info/patient/patient-number").text
                csn = "MTRX"+root.find("./case/case-info/case-id").text
                to_database = {
                    "MRN" : mrn,
                    "LName" : pat_lname,
                    "FName" : pat_fname,
                    "EncounterDOS" : encounter,
                    "LNameProvider" : provider_lname,
                    "FNameProvider" : provider_fname,
                    "NPI" : npi,
                    "SectionSysLabel" : sys_label,
                    "CSN" : csn,
                    "Filename" : file
                }

                statement = [
                    "SELECT * FROM #REMOVED# WHERE csn = :csn",
                    "AND SectionSysLabel = :label AND EncounterDOS = :dos"
                ]
                text = process.query(statement)
                query = conn.execute(text, csn=csn, label=sys_label, dos=encounter).fetchall()
                if query:
                    process.conn.execute(custom_reporting.update(None)\
                        .where(process.sqlalchemy.and_(\
                            custom_reporting.c.CSN==csn,\
                            custom_reporting.c.SectionSysLabel==sys_label,\
                            custom_reporting.c.EncounterDOS==encounter))\
                        .values(to_database))
                else:
                    conn.execute(custom_reporting.insert(to_database))
            process.track_files(file, process.section['table'])
        except Exception as exception:
            if process.bypass:
                process.send_email(file+"\n"+process.traceback.format_exc(), "MTRX Compensation Traceback")
            else:
                print(file)
                raise exception

if __name__ == "__main__":
    main()
        
