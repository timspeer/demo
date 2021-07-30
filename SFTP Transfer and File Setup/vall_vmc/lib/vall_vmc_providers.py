'''VALL VMC format providers'''
from datetime import datetime
from fnmatch import fnmatch

class Providers():
    '''format providers'''
    def __init__(self, fp_class:object):
        self.record:dict = fp_class.record
        self.fp_class:object = fp_class
        self.provider_list:list = []
        self.main()

    def main(self) -> None:
        '''main trigger'''
        self.anesthetists()
        self.surgeon()
        self.resp_prov()

    def anesthetists(self) -> None:
        '''form anesthetists'''
        total:int = 1
        for key in self.record.keys():
            if fnmatch(key, "ANES_STAFF*_NAME"):
                total += 1
        for num in range(1, total):
            if not self.record[f"ANES_STAFF{num}_NAME"]:
                continue
            name:list = self.record[f"ANES_STAFF{num}_NAME"].split(",")
            lname:str = name.pop(0).strip()
            name:list = " ".join(name).strip().split()
            if len(name[-1]) == 1:
                del name[-1]
            fname:str = " ".join(name).strip()
            to_database:dict = {
                "Rank" : num,
                "RawNameProvider" : self.record[f"ANES_STAFF{num}_NAME"],
                "LNameProvider" : lname,
                "FNameProvider" : fname,
                "NPIProvider" : self.record[f"ANES_STAFF{num}_NPI"],
                "TypeProvider" : "Anesthetist",
            }
            try:
                to_database["StartTime"] = \
                    datetime.strptime(self.record[f"ANES_STAFF{num}_START"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            try:
                to_database["StopTime"] = \
                    datetime.strptime(self.record[f"ANES_STAFF{num}_END"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            self.provider_list.append(to_database)

    def surgeon(self) -> None:
        '''get surgeon'''
        if not self.record["LOG_SURGEON_NAME"]:
            return
        name:list = self.record["LOG_SURGEON_NAME"].split(",")
        lname:str = name.pop(0).strip()
        name:list = " ".join(name).strip().split()
        try:
            if len(name[-1]) == 1:
                del name[-1]
        except IndexError:
            return
        fname:str = " ".join(name).strip()
        to_database:dict = {
            "Rank" : 1,
            "RawNameProvider" : self.record["LOG_SURGEON_NAME"],
            "LNameProvider" : lname,
            "FNameProvider" : fname,
            "NPIProvider" : self.record["LOG_SURGEON_NPI"],
            "TypeProvider" : "Surgeon",
        }
        self.provider_list.append(to_database)

    def resp_prov(self) -> None:
        '''get responsible provider'''
        to_database:dict = {
            "Rank" : 1,
            "RawNameProvider" : self.record["LOG_SURGEON_NAME"],
            "TypeProvider" : "Referring Provider",
        }
        self.provider_list.append(to_database)
