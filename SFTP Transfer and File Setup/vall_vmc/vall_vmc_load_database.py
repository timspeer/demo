'''VALL VMC Load Encounter'''
import os
import sys
import pandas
import numpy

from lib import vall_vmc_encounter
from lib import vall_vmc_insurance
from lib.vall_vmc_providers import Providers
from lib.vall_vmc_codes import Codes

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common import methods

def main(facility:str, bypass:str=None) -> None:
    '''main function'''
    fp_class:object = methods.FileProcess(facility, sftp=False)
    database:os.PathLike = os.path.join(os.path.dirname(__file__), fp_class.client["database"])
    table:str = "Setup"
    check_list:list = fp_class.check(
        table,
        os.path.join(fp_class.root, fp_class.client["csv_dir"]),
        database=database
        )
    for csv in check_list:
        print(csv)
        try:
            d_frame:object = pandas.read_csv(csv, sep="|", dtype=str)
            d_frame:object = d_frame.replace(numpy.nan, "", regex=True)
            d_list:list = d_frame.to_dict('records')
            for record in d_list:
                CreateRecord(fp_class, csv, record)
            fp_class.track_files(csv, table, database=database)
        except Exception as exception:
            if bypass:
                methods.send_email(methods.traceback.format_exc(), __doc__)
                continue
            print(csv)
            raise exception

class CreateRecord():
    '''csv records'''
    def __init__(self, fp_class:dict, csv:os.PathLike, record:dict):
        self.record:dict = record
        self.fp_class:object = fp_class
        self.states:dict = {
            '' : '',
            'Alabama': 'AL',
            'Alaska': 'AK',
            'Arizona': 'AZ',
            'Arkansas': 'AR',
            "Armed Forces Pacific" : "AP",
            "British Columbia": 'BC',
            'California': 'CA',
            'Colorado': 'CO',
            'Connecticut': 'CT',
            'Delaware': 'DE',
            'District of Columbia': 'DC',
            'Florida': 'FL',
            'Georgia': 'GA',
            'Hawaii': 'HI',
            'Idaho': 'ID',
            'Illinois': 'IL',
            'Indiana': 'IN',
            'Iowa': 'IA',
            'Kansas': 'KS',
            'Kentucky': 'KY',
            'Louisiana': 'LA',
            'Maine': 'ME',
            'Maryland': 'MD',
            'Massachusetts': 'MA',
            'Michigan': 'MI',
            'Minnesota': 'MN',
            'Mississippi': 'MS',
            'Missouri': 'MO',
            'Montana': 'MT',
            'Nebraska': 'NE',
            'Nevada': 'NV',
            'New Hampshire': 'NH',
            'New Jersey': 'NJ',
            'New Mexico': 'NM',
            'New York': 'NY',
            'North Carolina': 'NC',
            'North Dakota': 'ND',
            'Northern Mariana Islands':'MP',
            'Ohio': 'OH',
            'Oklahoma': 'OK',
            'Oregon': 'OR',
            'Palau': 'PW',
            'Pennsylvania': 'PA',
            'Puerto Rico': 'PR',
            'Rhode Island': 'RI',
            'South Carolina': 'SC',
            'South Dakota': 'SD',
            'Tennessee': 'TN',
            'Texas': 'TX',
            'Utah': 'UT',
            'Vermont': 'VT',
            'Virgin Islands': 'VI',
            'Virginia': 'VA',
            'Washington': 'WA',
            'West Virginia': 'WV',
            'Wisconsin': 'WI',
            'Wyoming': 'WY',
        }

        self.encounter_dict:dict = {
            "Client" : fp_class.client["client"],
            "Location" : fp_class.client["location"],
            "SourceFile" : csv,
            "CSN" : fp_class.client["client"]+fp_class.client["location"]+record["ANES_ENC_CSN_ID"]
        }
        self.enc_id:int = 0

        self.main()

    def main(self) -> None:
        '''main trigger'''
        self.encounter()
        self.insurance()
        self.providers()
        self.codes()

    def encounter(self) -> None:
        '''get and load encounter'''
        vall_vmc_encounter.main(self)
        self.enc_id:int = self.fp_class.load_database(
            self.encounter_dict["CSN"],
            "Encounter",
            self.fp_class.smi_encounter,
            self.encounter_dict
            )

    def insurance(self) -> None:
        '''load insurance'''
        insurance_list:list = vall_vmc_insurance.main(self)
        for insurance_dict in insurance_list:
            insurance_dict["CSN"] = self.encounter_dict["CSN"]
            insurance_dict["EncounterID"] = self.enc_id
            methods.plan_id(
                insurance_dict,
                self.encounter_dict["Location"],
                self.encounter_dict["Client"]
                )
            self.fp_class.load_database(
                insurance_dict["CSN"],
                "SMI_Insurance",
                self.fp_class.smi_insurance,
                insurance_dict
                )

    def providers(self) -> None:
        '''format and load providers'''
        provider_list:list = Providers(self).provider_list
        for prov_dict in provider_list:
            prov_dict["CSN"] = self.encounter_dict["CSN"]
            prov_dict["EncounterID"] = self.enc_id
            prov_dict["Client"] = self.encounter_dict["Client"]
            self.fp_class.load_database(
                prov_dict["CSN"],
                "SMI_Provider",
                self.fp_class.smi_providers,
                prov_dict
            )

    def codes(self) -> None:
        '''format and load codes'''
        code_list:list = Codes(self).code_list
        for code_dict in code_list:
            code_dict["CSN"] = self.encounter_dict["CSN"]
            code_dict["EncounterID"] = self.enc_id
            self.fp_class.load_database(
                code_dict["CSN"],
                "Codes",
                self.fp_class.smi_codes,
                code_dict
                )

if __name__ == "__main__":
    main("VALL_VMC")
