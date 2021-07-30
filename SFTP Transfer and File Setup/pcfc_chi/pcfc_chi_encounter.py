'''format encounter'''
import os
import re
from datetime import datetime

class Encounter():
    '''extract encounter info'''
    def __init__(self, raw:str, pdf:os.PathLike, client:dict):
        self.raw:str = raw
        self.pdf = pdf
        self.encounter_dict:dict = {
            "Client" : client['client'],
            "Location" : client['location']
        }
        self.main()

    def main(self) -> None:
        '''creates encounter dictionary'''
        self.get_csr_file_facility()
        self.get_mrn_csn_asa_patclass()
        self.get_demos()
        self.get_address()
        self.get_guarantor()
        self.get_event_times()
        self.get_procedure_anes_type()
        self.get_pain_info()

    def get_csr_file_facility(self) -> None:
        '''get CSR, Filenames, Facility, and MRN'''
        csrdt:datetime = datetime.fromtimestamp(os.path.getmtime(self.pdf))
        csrdt:datetime = csrdt.replace(hour=0, minute=0, second=0, microsecond=0)
        self.encounter_dict["CSR"] = csrdt

        self.encounter_dict["SourceFile"] = self.pdf
        self.encounter_dict["Filename"] = self.pdf

        room_facility:list = re.findall(r'(?<=Location:).*(?=\r\nPlan Summary)', self.raw)
        if not room_facility:
            facility:str = re.findall(r'(?<=Anesthesia Record\r\n).*', self.raw)[0].strip()
            self.encounter_dict["Facility"] = facility
            return
        room_facility:str = room_facility[0]
        room_facility:list = room_facility.split("/")
        self.encounter_dict["Facility"] = room_facility.pop(-1).strip()
        if room_facility:
            self.encounter_dict["Room"] = room_facility.pop(0).strip()

    def get_mrn_csn_asa_patclass(self) -> None:
        '''get mrn, csn, asa score, and patient class'''
        self.encounter_dict["MRN"] = re.findall(r'(?<=MRN:).*', self.raw)[0].strip()
        csn:str = re.findall(r'(?<=Contact Serial#:).*', self.raw)[0].strip()
        csn:str = self.encounter_dict['Client']+self.encounter_dict['Location']+csn
        self.encounter_dict['CSN'] = csn

        asa_score:str = re.findall(r'(?<=ASA status:).*\d{1}', self.raw)
        if asa_score:
            self.encounter_dict["ASAScore"] = asa_score[0].strip()

        patient_class:str = re.findall(r'(?<=Patient Class:).*(?=Unit)', self.raw)[0]
        self.encounter_dict["PatientClass"] = patient_class.strip()

    def get_demos(self) -> None:
        '''get name'''
        name:str = re.findall(r'(?<=Patient Name\r\n)[\s\S]*?(?=Sex\r\n)', self.raw)[0].strip()
        name:list = name.split(",")
        self.encounter_dict['LName'] = name.pop(0).strip()
        name:list = name[0].strip().split()
        self.encounter_dict['FName'] = name.pop(0).strip()
        if name:
            self.encounter_dict['MName'] = " ".join(name).strip()

        dob:str = re.findall(r'(?<=DOB\r\n)[\s\S]+?(?=SSN)', self.raw)[0].replace("\r\n", "")
        self.encounter_dict['DOB'] = datetime.strptime(dob, "%m/%d/%Y")

        self.encounter_dict['Sex'] = re.findall(r'(?<=Sex\r\n).*', self.raw)[0].strip()

        try:
            phone:str = re.findall(r'(?<=Phone\r\n)[\s\S]*?(?=Case Summary)', self.raw)[0].strip()
        except IndexError:
            phone:list = re.findall(
                r'(?<=Contact Numbers \(Temporary\)\r\n)[\s\S]*?(?=Case Summary)', self.raw
                )
            if phone:
                phone:str = phone[0].strip()
            else:
                phone:str = str()
        phone:list = phone.split("\r\n")
        for phone_num in phone:
            phone_num:str
            if "(Home)" in phone_num:
                self.encounter_dict['HomePhone'] = re.findall(
                    r'\d{3}[-]?\d{3}[-]?\d{4}', phone_num
                    )[0].strip()
            if "(Mobile)" in phone_num:
                self.encounter_dict['MobilePhone'] = re.findall(
                    r'\d{3}-\d{3}-\d{4}', phone_num
                    )[0].strip()

        marital_status:str = re.findall(
            r'(?<=Marital Staus).*(?=Email)', self.raw
            )[0].strip() #mispelled on pdf
        self.encounter_dict["MaritalStatus"] = marital_status

    def get_address(self) -> None:
        '''get address'''
        try:
            address:str = re.findall(r'(?<=Address\r\n)[\s\S]*?(?=Phone)', self.raw)[0].strip()
        except IndexError:
            address:list = re.findall(
                r'(?<=Address \(Temporary\)\r\n)[\s\S]*?(?=Contact Numbers)', self.raw
                )
            if address:
                address:str = address[0].strip()
            else:
                return
        address:list = address.split("\r\n")
        csz:list = address.pop(-1)
        if re.match(r'^\d{4}$', csz):
            csz:str = address.pop(-1)+" "+csz
        csz:list = csz.split()
        if len(csz) != 1:
            if re.match(r'^\d{4}$', csz[-1]):
                zip_:str = csz.pop(-1)
                csz[-1] = csz[-1]+zip_
            self.encounter_dict["Zip"] = csz.pop(-1)
            self.encounter_dict['State'] = csz.pop(-1)
            self.encounter_dict['City'] = " ".join(csz).strip()
        self.encounter_dict["Address"] = " ".join(address).strip()

    def get_guarantor(self) -> None:
        '''get guarantor information'''
        name:str = re.findall(r'(?<=Guarantor:).*?(?=DOB)', self.raw)[0].strip()
        name:list = name.split(",")

        self.encounter_dict['LNameGuarantor'] = name.pop(0)
        try:
            name:list = name[0].split()
            self.encounter_dict['FNameGuarantor'] = name.pop(0)
            if name:
                self.encounter_dict["MNameGuarantor"] = name[0]
        except IndexError:
            pass

        guar_sections:str = re.findall(r'Guarantor:[\s\S]*?GUARANTOR EMPLOYER', self.raw)[0]
        guar_sections:list = guar_sections.split('\r\n')

        dob:str = re.findall(r'(?<=DOB:).*', guar_sections.pop(0))[0].strip()
        if dob:
            dob:datetime = datetime.strptime(dob, "%m/%d/%Y")
        self.encounter_dict['DOBGuarantor'] = dob

        address_sex:str = guar_sections.pop(0)
        address:str = re.findall(r'(?<=Address:).*?(?=Sex)', address_sex)[0].strip()
        self.encounter_dict['AddressGuarantor'] = address
        self.encounter_dict['SexGuarantor'] = re.findall(r'(?<=Sex:).*', address_sex)[0].strip()

        csz:list = guar_sections.pop(0).split(",")
        if "".join(csz):
            self.encounter_dict["CityGuarantor"] = csz.pop(0).strip()
            csz:list = csz[0].strip().split()
            self.encounter_dict["StateGuarantor"] = csz.pop(0).strip()
            self.encounter_dict["ZipGuarantor"] = csz[0].strip()

        relation_phone: str = guar_sections.pop(0)
        self.encounter_dict["RelationshipGuarantor"] = re.findall(
            r'(?<=Relation to Patient:).*?(?=Primary)', relation_phone
            )[0].strip()
        phone:str = re.findall(r'(?<=Primary Phone:).*', relation_phone)[0].strip()
        if phone:
            phone:str = phone.split()[0]
            self.encounter_dict["HomePhoneGuarantor"] = phone

        employer:str = re.findall(r'(?<=Employer:).*(?=Status)', self.raw)[0].strip()
        if employer:
            self.encounter_dict["EmployerGuarantor"] = employer

    def get_event_times(self) -> None:
        '''get dos and anesthesia times'''
        self.encounter_dict['AnesthesiaStop'] = None
        if "Emergent" in self.raw:
            self.encounter_dict["Emergency"] = 1
        dos:str = re.findall(r'(?<=Encounter Date:).*', self.raw)[0].strip()
        dos:datetime = datetime.strptime(dos, "%m/%d/%Y")
        self.encounter_dict['DOS'] = dos
        if "No anesthesia events file" in self.raw:
            return

        events:str = re.findall(
            r'(?<=Date Time Event\r\n)[\s\S]*?'
            r'(?:Transfer of Care \& Report Given|Baby Delivered)',
            self.raw
            )
        if not events:
            return
        events:list = re.findall(r'.*\d{4}.*', events[0])

        current_dos:str = str()
        for event in events:
            new_dos:list = re.findall(r'^\d{1,2}/\d{1,2}/\d{4}[ ]+\d{4}', event)
            if new_dos:
                current_dos:str = new_dos[0].split()[0]
            start:list = re.findall(r'\d{4}[ ]+(?=Anesthesia Start)', event)
            if start:
                start:str = current_dos+" "+start[0].strip()
                self.encounter_dict['AnesthesiaStart'] = datetime.strptime(start, "%m/%d/%Y %H%M")
            induction:list = re.findall(r'\d{4}[ ]+(?=Induction)', event)
            if induction:
                induction:str = current_dos+" "+induction[0].strip()
                self.encounter_dict['InductionDT'] = datetime.strptime(induction, "%m/%d/%Y %H%M")
            epidural_to_csection:list = re.findall(r'\d{4}[ ]+(?=Epidural to C-Section)', event)
            if epidural_to_csection:
                epidural_to_csection:str = current_dos+" "+epidural_to_csection[0].strip()
                self.encounter_dict['EpiduralToCSectionDT'] =\
                    datetime.strptime(epidural_to_csection, "%m/%d/%Y %H%M")
            stop:list = re.findall(
                r'\d{4}[ ]+(?=Transfer of Care \& Report Given|Stop Data Collection)', event
                )
            if stop:
                stop:str = current_dos+" "+stop[0].strip()
                self.encounter_dict['AnesthesiaStop'] = datetime.strptime(stop, "%m/%d/%Y %H%M")

    def get_procedure_anes_type(self) -> None:
        '''format procedure and anes type'''
        procedure:str = re.findall(r'(?<=Procedure \[Code\]\r\n)[\s\S]*?(?=Diagnosis)', self.raw)[0]
        procedure:str = procedure.split("[")[0].strip().replace("\r\n", ' ')
        self.encounter_dict['PrimaryProcedure'] = procedure

        anes_type:list = re.findall(r'(?<=Final Anesthesia Type\r\n).*', self.raw)[0].strip()
        if anes_type == "Primary Coverage":
            anes_type:list = re.findall(r'.*(?=\r\nMedications Administered)', self.raw)[0].strip()

        self.encounter_dict["AnesthesiaType"] = anes_type

    def get_pain_info(self) -> None:
        '''get block info'''
        pain:list = re.findall(r'.*post-op pain.*', self.raw)
        if pain:
            self.encounter_dict['PainBlock'] = 1
            if "surgeon's request" in " ".join(pain):
                self.encounter_dict['SurgeonRequestedBlock'] = 1
