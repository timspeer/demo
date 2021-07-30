'''VALL VMC Encounter'''
from datetime import datetime

def main(self) -> dict:
    '''format encounter dict'''
    guarantor:list = self.record["GUARANTOR_NAME"].split(',')
    lname:str = guarantor[0]
    fname:str = guarantor[1].split()[0]
    try:
        mname:str = guarantor[1].split()[1]
    except IndexError:
        mname = None
    to_database:dict = {
        "MRN" : self.record["PAT_MRN_ID"],
        "LName" : self.record["PAT_LAST_NAME"],
        "FName" : self.record["PAT_FIRST_NAME"],
        "MName" : self.record["PAT_MIDDLE_NAME"],
        "DOB" : datetime.strptime(self.record["BIRTH_DATE"], "%Y-%m-%d %H:%M:%S"),
        "Sex" : self.record["Sex"],
        "SSN" : self.record["SSN"],    
        "Address" : f"{self.record['ADD_LINE_1']} {self.record['ADD_LINE_2']}",
        "City" : self.record["CITY"],
        "State" : self.states[self.record["STATE"]],
        "Zip" : self.record["ZIP"],
        "HomePhone" : self.record["HOME_PHONE"],
        "MobilePhone" : self.record["MOBILE_PHONE"],
        "EmailAddress" : self.record["EMAIL_ADDRESS"],
        "MaritalStatus" : self.record["MARITAL_STATUS"],
        "LNameGuarantor" : fname,
        "FNameGuarantor" : lname,
        "MNameGuarantor" : mname,
        "AddressGuarantor" : f'{self.record["GUAR_ADDR_1"]} {self.record["GUAR_ADDR_2"]}',
        "CityGuarantor" : self.record["GUAR_CITY"],
        "StateGuarantor" : self.states[self.record["GUAR_STATE"]],
        "ZipGuarantor" : self.record["GUAR_ZIP"],
        "HomePhoneGuarantor" : self.record["GUAR_HOME_PHONE"],
        "DOBGuarantor" : datetime.strptime(self.record["GUAR_BIRTH_DATE"], "%Y-%m-%d %H:%M:%S"),
        "SexGuarantor" : self.record["GUAR_SEX"],
        "SSNGuarantor" : self.record["GUAR_SSN"],
        "RelationshipGuarantor" : self.record["GUARANTOR_PATIENT_RELATIONSHIP"],
        "DOS" : datetime.strptime(self.record["AN_DATE"], "%m/%d/%Y"),
        "AnesthesiaStart" : self.record["ANESTHESIA_START_DTTM"],
        "AnesthesiaStop" : self.record["ANESTHESIA_STOP_DTTM"],
        "AnesthesiaType" : self.record["ANESTHESIA_TYPE"],
        "PrimaryProcedure" : self.record["PRIMARY_PROCEDURE"],
        "Room" : self.record["LOC_NAME"],
        "Facility" : f'{self.record["HOSPITAL_AREA_ID"]} {self.record["LOCATION_ABBR"]}',
        "ASAScore" : self.record["ASA_SCORE"],
        "PatientClass" : self.record["ADT_PAT_CLASS"],
        "Language" : self.record["LANGUAGE"]
    }
    self.encounter_dict.update(to_database)
