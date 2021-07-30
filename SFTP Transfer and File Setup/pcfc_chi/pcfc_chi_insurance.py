'''PCFC CHI Insurance formatting'''
import re
from datetime import datetime

class Insurance():
    '''format insurance information into dictionary'''
    def __init__(self, table:str):
        self.table:str = table
        self.rel:list = list()
        self.group_nums:list = list()
        self.insurance_list:list = list()
        self.active_insurance:str = str()

        self.main()

    def main(self) -> None:
        '''main handler'''
        if "Patient has no active insurance coverage" in self.table:
            return
        rel:list = re.findall(r'P[a]?t.[ ]+Rel.[ ]+to[ ]+Subscriber:.*', self.table)
        self.rel:list = [item.strip().split(":")[-1].strip() for item in rel]
        self.rel:list = [item.strip() for item in self.rel if item.strip()]

        group_nums:list = re.findall(r'Group[ ]+Number:.*?(?=Subscriber)', self.table)
        self.group_nums:list = [item.split(":")[-1].strip() for item in group_nums]

        self.insurance()

    def insurance(self):
        '''create insurance list'''
        coverage:list = re.findall(
            r'Employer/Plan[ ]+Group[\s\S]*?'
            r'(?:Payor[ ]+Plan[ ]+Insurance[ ]+Group|Anesthesia[ ]+Record[ ]+ID)',
            self.table
            )
        for idx, cov in enumerate(coverage):
            insurance_dict:dict = {
                "AddressPayor" : str(),
                "CityPayor" : str(),
                "StatePayor" : str(),
                "ZipPayor" : str(),
                "Rank" : idx+1
            }
            if len(self.rel) >= idx+1:
                insurance_dict['RelationshipToPatient'] = self.rel[idx]
            cov:list = [item.strip() for item in cov.split("\r\n") if item]
            cov:list = [[x for x in item.split("  ") if x] for item in cov][1:]

            payor_plan_group:list = cov.pop(0)
            self.get_payor_plan_group(payor_plan_group, insurance_dict, idx)

            if cov[0] != ['Subscriber Name', 'Subscriber Birth Date', 'Member ID']:
                del cov[0]
            address:list = [item.strip() for item in cov.pop(0)]
            cov[0] = [item.strip() for item in cov[0]]
            if address == ['Subscriber Name', 'Subscriber Birth Date', 'Member ID']:
                address:None = None
            else:
                while cov[0] != ['Subscriber Name', 'Subscriber Birth Date', 'Member ID']:
                    address.append(cov.pop(0))
                    cov[0] = [item.strip() for item in cov[0]]
            self.get_address(address, insurance_dict)
            self.get_subscriber_info(cov, insurance_dict)
            self.insurance_list.append(insurance_dict)

    def get_payor_plan_group(self, payor_plan_group:list, insurance_dict:dict, idx:int) -> None:
        '''format payor plan and group'''
        insurance_dict['PayorName'] = payor_plan_group.pop(0).strip()
        insurance_dict['PlanName'] = payor_plan_group.pop(0).strip()
        if payor_plan_group:
            insurance_dict['GroupNumber'] = payor_plan_group[0].strip()
            if payor_plan_group:
                insurance_dict['PlanName'] = \
                    insurance_dict['PlanName']+insurance_dict['GroupNumber']
                insurance_dict['GroupNumber'] = payor_plan_group.pop(0).strip()
        elif idx < 2 and self.group_nums[idx] and self.group_nums[idx] != "N/A":
            insurance_dict['GroupNumber'] = self.group_nums[idx].strip()

    @staticmethod
    def get_address(address:list, insurance_dict:dict):
        '''get address'''
        if not address:
            return
        csz:list = address.pop(-1)[0].split()
        if not csz or len(csz) == 1:
            return
        insurance_dict["ZipPayor"] = csz.pop(-1).strip()
        insurance_dict['StatePayor'] = csz.pop(-1).strip()
        insurance_dict['CityPayor'] = " ".join(csz).strip()

        del_list:list = [
            ['Entered']
        ]

        if address[-1] in del_list:
            del address[-1]

        if isinstance(address[-1], list):
            address_line:str = str()
            while isinstance(address[-1], list):
                address_line:str = (address.pop(-1).pop(0)+" "+address_line).strip()
            if not re.match(r'[ ]?\d{3}-\d{3}-\d{4}', address[0])\
                            and address[0].strip() != "Payor Plan Address":
                address_line:str = (address.pop(0)+" "+address_line).strip()
        else:
            address_line:str = address.pop(0)
        insurance_dict['AddressPayor'] = address_line

    @staticmethod
    def get_subscriber_info(cov:list, insurance_dict:dict) -> None:
        '''get subscriber info'''
        if cov[0] == ['Subscriber Name', 'Subscriber Birth Date', 'Member ID']:
            del cov[0]
        name_dob_num:list = cov.pop(0)
        if "," in name_dob_num[0]:
            name:list = name_dob_num.pop(0).split(",")
            insurance_dict['LNameSubscriber'] = name.pop(0).strip()
            name:list = name[0].split()
            if len(name) > 1:
                insurance_dict['MNameSubscriber'] = name.pop(-1).strip()
            insurance_dict['FNameSubscriber'] = " ".join(name).strip()
        try:
            dob:datetime = datetime.strptime(name_dob_num[0].strip(), "%m/%d/%Y")
            insurance_dict['DOBSubscriber'] = dob
            del name_dob_num[0]
        except ValueError:
            pass
        if name_dob_num:
            insurance_dict['SubscriberNumber'] = name_dob_num[0].strip()
