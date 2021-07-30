'''PCFC CHI Codes'''
import re

class Codes():
    '''format codes'''
    def __init__(self, raw:str):
        self.raw:str = raw
        self.codes_list:list = list()

        self.main()

    def main(self) -> None:
        '''main handler'''
        self.cpt_codes()
        self.dx_codes()
        self.medical_hx()

    def cpt_codes(self) -> None:
        '''extract cpt codes'''
        codes:list = re.findall(
            r'(?<=Procedure \[Code\])[\s\S]*?(?=Diagnosis \[Codes\])', self.raw
            )
        if not codes:
            return

        codes:list = re.findall(r'[\s\S]*?(?:\[.*\]|$)', codes[0].strip())
        codes:list = [item.strip().replace("\r\n", " ") for item in codes if item.strip()]

        for idx, code in enumerate(codes):
            code:list = code.split("[")
            description:str = code.pop(0)
            if code:
                cpt:str = code[0].strip("]").strip().split()[0]
            else:
                cpt:None = None
            code_dict:dict = {
               "Rank" : idx+1,
               "Description" : description.strip(),
               "Type" : "CPT",
               "Code" : cpt
            }
            self.codes_list.append(code_dict)

    def dx_codes(self) -> None:
        '''extract DX codes'''
        if "No diagnosis recorded" in self.raw:
            return
        end_caps:list = [
            r'Preoperative diagnosis',
            r'Medication Calculated',
            r'Most Recent Value',
            r'Date Time Event',
            r'Final Anesthesia',
            r'Staff',
            r'Preoperative Postoperative',
            r'Anesthesia TEE Note'
        ]
        end:str = fr"(?={'|'.join(end_caps)})"
        codes:list = re.findall(r'(?<=Diagnosis \[Codes\])[\s\S]*?'+end, self.raw)

        codes:list = re.findall(r'[\s\S]*?(?:\]|$)', codes[0].strip())
        codes:list = [item.strip() for item in codes if item.strip()]

        rank:int = 1
        for code in codes:
            code:list = code.split("[")
            description:str = code.pop(0)
            if code:
                diag:list = code[0].replace("]", "").split(",")
                for dx_code in diag:
                    dx_dict:dict = {
                        "Description" : description.strip(),
                        "Type" : "DX",
                        "Code" : dx_code
                    }
                    if dx_dict not in self.codes_list:
                        dx_dict["Rank"] = rank
                        self.codes_list.append(dx_dict)
                        rank += 1
            else:
                dx_dict:dict = {
                    "Description" : description.strip(),
                    "Type" : "DX",
                }
                if dx_dict not in self.codes_list:
                    dx_dict["Rank"] = rank
                    self.codes_list.append(dx_dict)
                    rank += 1

    def medical_hx(self) -> None:
        '''extract medical history'''
        history:list = re.findall(r'(?<=Other Medical History\r\n)[\s\S]*', self.raw)
        if not history:
            return
        history:str = re.sub(
            r'Revision History[\s\S]*(?:History Comments History Comments|$)', '', history[0]
            )
        history:list = history.split("\r\n")
        history:list = [item.strip() for item in history if item.strip()]
        for idx, his in enumerate(history):
            hx_dict:dict = {
                "Rank" : idx+1,
                "Type" : "HX",
                "Description" : his.strip()
            }
            self.codes_list.append(hx_dict)