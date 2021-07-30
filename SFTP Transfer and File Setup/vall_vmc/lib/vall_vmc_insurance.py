'''VALL VMC format insurance'''
from datetime import datetime
from fnmatch import fnmatch

def main(self:object) -> list:
    '''format insurance'''
    return_list:list = []
    total:int = 1
    for key in self.record.keys():
        if  fnmatch(key, "INS*_SUBSCRIBER_NAME"):
            total += 1
    for num in range(1, total):
        if not self.record[f"INS{num}_CARRIER_NAME"]:
            continue
        sub_name:str = self.record[f"INS{num}_SUBSCRIBER_NAME"]
        if sub_name:
            sub_name:list = sub_name.split(',')
            sub_lname:str = sub_name[0]
            sub_fname:str = sub_name[1].split()[0]
            try:
                sub_mname:str = sub_name[1].split()[1]
            except IndexError:
                sub_mname = None
        else:
            sub_lname, sub_fname, sub_mname = None, None, None
        dob:str = self.record[f"INS{num}_SUBSCRIBER_DATE_OF_BIRTH"]
        if dob:
            dob:datetime = datetime.strptime(dob, "%Y-%m-%d %H:%M:%S")
        to_database:dict = {
            "Rank" : num,
            "PayorName" : self.record[f"INS{num}_CARRIER_NAME"],
            "PlanName" : self.record[f"INS{num}_BENEFIT_PLAN_NAME"],
            "AddressPayor" : f'{self.record[f"INS{num}_CARRIER_STREET1"]} ' \
                f'{self.record[f"INS{num}_CARRIER_STREET2"]}',
            "CityPayor" : self.record[f"INS{num}_CARRIER_CITY"],
            "StatePayor" : self.states[self.record[f"INS{num}_CARRIER_STATE"]],
            "ZipPayor" : self.record[f"INS{num}_CARRIER_ZIP_CODE"],
            "GroupName" : self.record[f"INS{num}_POLICY_GROUP_NAME"],
            "GroupNumber" : self.record[f"INS{num}_POLICY_GROUP_NO"],
            "RelationshipToPatient" : self.record[f'INS{num}_POLICY_PATIENT_RELATIONSHIP'],
            "SubscriberNumber" : self.record[f"INS{num}_SUBSCR_NUM"],
            "LNameSubscriber" : sub_lname,
            "FNameSubscriber" : sub_fname,
            "MNameSubscriber" : sub_mname,
            "AddressSubscriber" : f'{self.record[f"INS{num}_SUBSCRIBER_STREET1"]} ' \
                f'{self.record[f"INS{num}_SUBSCRIBER_STREET2"]}',
            "CitySubscriber" : self.record[f"INS{num}_SUBSCRIBER_CITY"],
            "StateSubscriber" : self.states[self.record[f"INS{num}_SUBSCRIBER_STATE"]],
            "ZipSubscriber" : self.record[f"INS{num}_SUBSCRIBER_ZIP_CODE"],
            "PhoneSubscriber" : self.record[f"INS{num}_SUBSCRIBER_PHONE"],
            "SexSubscriber" : self.record[f"INS{num}_SUBSCRIBER_SEX"],
            "SSNSubscriber" : self.record[f"INS{num}_SUBSCRIBER_SSN"],
            "DOBSubscriber" : dob
        }
        return_list.append(to_database)
    return return_list
