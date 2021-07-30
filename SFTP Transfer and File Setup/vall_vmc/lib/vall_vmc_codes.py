'''VALL VMC format codes'''
import re
from fnmatch import fnmatch

class Codes():
    '''format codes'''
    def __init__(self, fp_class:object):
        self.record:dict = fp_class.record
        self.fp_class:object = fp_class
        self.code_list:list = []

        self.main()

    def main(self) -> None:
        '''main trigger'''
        self.cpt()
        self.log_preop()
        self.post_dx()
        self.icd10()
        self.hx_dx()

    def cpt(self) -> None:
        '''format cpt'''
        to_database:dict = {
            "Rank" : 1,
            "Type" : "CPT",
            "Code" : self.record["BILLING_CPT_PRIMARY_SECONDARY"]
        }
        self.code_list.append(to_database)

    def log_preop(self) -> None:
        '''format preop dx'''
        des:str = self.record["LOG_PREOP_DX"]
        codes:list = re.findall(r'.*\]', des)
        if not codes:
            to_database:dict = {
                "Rank" : 1,
                "Description" : des,
                "Type" : "PreDX"
            }
            self.code_list.append(to_database)
            return
        for section in codes:
            description:str = re.findall(r'.*?(?=\[)', section)[0].strip()
            multi:list = re.findall(r'(?<=\[).*?(?=\])', section)[0].strip().split(",")
            for idx, multi_dx in enumerate(multi):
                to_database:dict = {
                    "Rank" : idx+1,
                    "Description" : description,
                    "Type" : "PreDX",
                    "Code" : multi_dx.strip()
                }
                self.code_list.append(to_database)

    def post_dx(self) -> None:
        '''format post op dx'''
        total:int = 1
        for key in self.record.keys():
            if  fnmatch(key, "BILLING_POSTOP_DIAG?"):
                total += 1
        for num in range(1, total):
            if not self.record[f"BILLING_POSTOP_DIAG{num}"]:
                continue
            to_database:dict = {
                "Rank" : num,
                "Description" : self.record[f"BILLING_POSTOP_DIAG_NAME{num}"],
                "Code" : self.record[f"BILLING_POSTOP_DIAG{num}"],
                "Type" : "PostDX"
            }
            self.code_list.append(to_database)

    def icd10(self) -> None:
        '''get icd10 codes'''
        if not self.record["LOG_PREOP_DX_ICD10"]:
            return
        description:str = self.record["LOG_PREOP_DX_ICD10"].split("[")[0].strip()
        codes:list = self.record["LOG_POSTOP_DX_ICD10"].split(",")
        for idx, code in enumerate(codes):
            to_database:dict = {
                "Rank" : idx+1,
                "Description" : description,
                "Code" : code,
                "Type" : "ICD10"
            }
            self.code_list.append(to_database)

    def hx_dx(self) -> None:
        '''format hx_dx'''
        total:int = 1
        for key in self.record.keys():
            if  fnmatch(key, "MEDICAL_HX_DX_NAME?"):
                total += 1
        for num in range(1, total):
            if not self.record[f"MEDICAL_HX_DX_NAME{num}"]:
                continue
            to_database:dict = {
                "Rank" : num,
                "Description" : self.record[f"MEDICAL_HX_DX_NAME{num}"],
                "Code" : self.record[f"MEDICAL_HX_DX{num}"],
                "Type" : "HX"
            }
            self.code_list.append(to_database)
