'''PCFC CHI Load Database'''
import os
import sys
import re
import typing

from pcfc_chi_encounter import Encounter
from pcfc_chi_insurance import Insurance
from pcfc_chi_providers import Providers
from pcfc_chi_codes import Codes

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import methods

class Main(methods.FileProcess):
    '''main class'''
    def __init__(self, facility:str, bypass:str=None):
        print(__doc__)
        super().__init__(facility, sftp=False)
        self.bypass:str = bypass
        self.database:os.PathLike = os.path.join(
            os.path.dirname(__file__), 'pcfc_chi_filetracker.db'
            )
        self.table:str = "Setup"
        self.check_list:list = self.check(
            self.table,
            os.path.join(self.root, self.client["pdf_dir"]),
            database=self.database
            )
        self.main()

    def main(self) -> None:
        '''import pdf to encounter'''
        for pdf in self.check_list:
            try:
                pdf:os.PathLike = os.path.join(self.root, self.client["pdf_dir"], pdf)
                print(pdf)

                raw:str = methods.pdf_to_text(pdf, "raw")
                table:str = methods.pdf_to_text(pdf, "table")

                replace_list = [
                    r'.*\(continued\)\r\n'
                ]
                for rep in replace_list:
                    raw:str = re.sub(rep, '', raw)

                encounter_dict, id_ = self.encounter(raw, pdf)

                self.insurance(table, id_, encounter_dict['CSN'])

                self.providers(raw, encounter_dict, id_)

                self.codes(raw, encounter_dict['CSN'], id_)

                self.track_files(pdf, self.table, database=self.database)
            except Exception as exception:
                if self.bypass:
                    methods.send_email(methods.traceback.format_exc(), __doc__)
                    continue
                print(pdf)
                raise exception

    def encounter(self, raw:str, pdf:os.PathLike) -> typing.Tuple[dict, int]:
        '''load Encounter'''
        encounter_dict:dict = Encounter(raw, pdf, self.client).encounter_dict
        id_:int = self.load_database(
            csn=encounter_dict['CSN'],
            table="Encounter",
            table_object=self.smi_encounter,
            original_dictionary=encounter_dict
        )
        return encounter_dict, id_

    def insurance(self, table:str, id_:int, csn:str) -> None:
        '''load insurance'''
        insurance_list:list = Insurance(table).insurance_list
        for ins in insurance_list:
            methods.plan_id(ins, self.client['location'], self.client['client'])
            ins['EncounterID'] = id_
            ins['CSN'] = csn
            self.load_database(csn, "SMI_Insurance", self.smi_insurance, ins)

    def providers(self, raw:str, encounter_dict:dict, id_:int) -> None:
        '''load providers'''
        provider_list:list = Providers(
            raw=raw,
            dos=encounter_dict['DOS'],
            anes_stop=encounter_dict['AnesthesiaStop']
            ).provider_list
        for prov_dict in provider_list:
            prov_dict['CSN'] = encounter_dict['CSN']
            prov_dict['EncounterID'] = id_
            prov_dict['Client'] = self.client['client']
            self.load_database(encounter_dict['CSN'], "SMI_Provider", self.smi_providers, prov_dict)

    def codes(self, raw:str, csn:str, id_:int) -> None:
        '''load codes'''
        code_list:list = Codes(raw).codes_list
        for code_dict in code_list:
            code_dict["CSN"] = csn
            code_dict['EncounterID'] = id_
            self.load_database(csn, "Codes", self.smi_codes, code_dict)

if __name__ == "__main__":
    Main("PCFC_CHI")
