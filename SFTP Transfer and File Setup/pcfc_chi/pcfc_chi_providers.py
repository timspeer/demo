'''format provider list'''
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Providers():
    '''format provider information into dictionary'''
    def __init__(self, raw:str, dos:datetime, anes_stop:datetime):
        self.raw:str = raw
        self.provider_list:list = list()
        self.dos:datetime = dos
        self.anes_stop:datetime = anes_stop
        self.main()

    def main(self) -> None:
        '''main handler'''
        self.anesthestists()
        surgeon:list = re.findall(r'(?<=Surgeon:).*', self.raw)
        if surgeon:
            surgeon:str = surgeon[0].split(",")[0].strip()
            surgeon_dict:dict = {
                "Rank" : 1,
                "TypeProvider" : "Surgeon",
                "RawNameProvider" : surgeon
            }
            self.provider_list.append(surgeon_dict)
        resp_prov:list = re.findall(r'(?<=Responsible Provider:).*', self.raw)
        if resp_prov:
            resp_prov:str = resp_prov[0].split(",")[0].strip()
            resp_dict:dict = {
                "Rank" : 1,
                "TypeProvider" : "Responsible Provider",
                "RawNameProvider" : resp_prov
            }
            self.provider_list.append(resp_dict)

    def anesthestists(self) -> None:
        '''find anesthetists'''
        if "No responsible staff documented" in self.raw:
            return
        staff:str = re.findall(r'Staff[\s\S]*?Final Anesthesia Type', self.raw)[0]
        anes_list:list = re.findall(r'.*', staff)[4:]
        anes_list:list = [item for item in anes_list if re.match(r'.*,.* \d{4} .*\r', item)]
        current_dos:datetime = self.dos
        for idx, provider in enumerate(anes_list):
            provider:list = provider.split(",")
            name:str = provider.pop(0)
            provider:list = provider[0].split()
            if len(provider[-1]) != 1:
                break
            provider:list = provider[:-1]
            try:
                stop:datetime = datetime.strptime(
                    current_dos.strftime("%Y-%m-%d")+" "+provider.pop(-1), "%Y-%m-%d %H%M"
                    )
            except ValueError:
                return
            try:
                start:datetime = datetime.strptime(
                    current_dos.strftime("%Y-%m-%d")+" "+provider.pop(-1), "%Y-%m-%d %H%M"
                    )
            except ValueError:
                start:datetime = stop
                stop:None = None

            if start and stop:
                if stop < start:
                    stop:datetime = stop + relativedelta(days=1)

            if start < current_dos:
                start:datetime = start + relativedelta(days=1)
                try:
                    stop:datetime = stop + relativedelta(days=1)
                except TypeError:
                    stop:datetime = self.anes_stop

            current_dos:datetime = stop

            if not stop:
                stop:datetime = self.anes_stop

            provider_dict:dict = {
                "Rank" : idx+1,
                "TypeProvider" : "Anesthetist",
                "RawNameProvider" : name,
                "StartTime" : start,
                "StopTime" : stop
            }
            self.provider_list.append(provider_dict)
