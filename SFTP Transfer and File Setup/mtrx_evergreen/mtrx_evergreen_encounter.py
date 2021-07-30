'''format basic encounter'''
import re
from datetime import datetime

def main(csrdt, client, file, root) -> dict:
    '''format the dictionary'''
    def try_catch(to_database_field, temp_dict_field):
        try:
            to_database[to_database_field] = temp_dict[temp_dict_field]
        except KeyError:
            pass
    to_database = {
        "CSR" : csrdt,
        "Client" : client,
        "SourceFile" : file,
        "Location" : "Evergreen",
        "MRN" : ''
    }
    node = root.find("./case/case-info")
    if node.find("./patient/patient-number").text:
        to_database["MRN"] = node.find("./patient/patient-number").text
    to_database["CSN"] = client+node.find("./case-id").text
    to_database["LName"] = node.find("./patient/last-name").text
    to_database["FName"] = node.find("./patient/first-name").text
    to_database["MName"] = node.find("./patient/middle-name").text
    to_database["DOB"] = node.find("./patient/date-of-birth").text
    to_database["Sex"] = node.find("./sex").text
    to_database["EmailAddress"] = node.find("./patient/email").text
    to_database["DOS"] = datetime.fromisoformat(node.find("./scheduled-at").text)

    address_list = node.findall("./demographics-and-insurance-data/demographics-and-insurance-datum")

    temp_dict = {}
    for item in address_list:
        keys = item.findall("./key")
        vals = item.findall("./value")
        for key in keys:
            temp_dict[key.text] = ''
        for idx, val in enumerate(vals):
            temp_dict[keys[idx].text] = val.text
    try:
        to_database["Address"] = temp_dict["pt_address_1"]+" "+temp_dict["pt_address_2"]
    except KeyError:
        try_catch("Address", "pt_address_1")
    try_catch("Zip", "pt_postal_code")
    try_catch("City", "pt_city")
    try_catch("State", "pt_state_territory")
    try:
        to_database["HomePhone"] = temp_dict["phone"]
        for rep in ["(", ")", "_"]:
            to_database["HomePhone"] = to_database["HomePhone"].replace(rep, "")
    except KeyError:
        pass
    try_catch("MaritalStatus", "pt_marital_status")
    try_catch("LNameGuarantor", "gt_last_name")
    try_catch("FNameGuarantor", "gt_first_name")
    try_catch("MNameGuarantor", "gt_middle_name")
    try:
        to_database["AddressGuarantor"] = temp_dict["gt_address_1"]+" "+temp_dict["gt_address_2"]
    except KeyError:
            try_catch("AddressGuarantor", "gt_address_1")
    try_catch("CityGuarantor", "gt_city")
    try_catch("StateGuarantor", "gt_state_territory")
    try_catch("ZipGuarantor", "gt_postal_code")
    try:
        to_database["HomePhoneGuarantor"] = temp_dict["gt_area_code"]+temp_dict["gt_phone_number"]
        for rep in ["(", ")", "-"]:
            to_database["HomePhoneGuarantor"] = to_database["HomePhoneGuarantor"].replace(rep, "")
    except KeyError:
        pass
    try:
        to_database["DOBGuarantor"] = datetime.strptime(temp_dict["gt_date_of_birth"], "%Y%m%d")
    except KeyError:
        pass
    try_catch("SexGuarantor", "gt_gender")
    try_catch("RelationshipGuarantor", "gt_relationship_to_patient")
    try_catch("EmployerGuarantor", "gt_employer_name")
    
    events = node.findall("./events/key-events/key-event")
    for event in events:
        label = event.find("./sysid").text
        if label == "anesthesia_start":
            to_database["AnesthesiaStart"] = datetime.fromisoformat(event.find("./performed-at").text)
        if label == "induction":
            to_database["InductionDT"] = datetime.fromisoformat(event.find("./performed-at").text)
        if label == "anesthesia_stop":
            to_database["AnesthesiaStop"] = datetime.fromisoformat(event.find("./performed-at").text)
            
    to_database["PatientClass"] = node.find("./in-out-status").text
    try:
        to_database["AnesthesiaType"] = node.find("./anesthetic-types/anesthetic-type/sysid").text
    except AttributeError:
        pass
    to_database["PrimaryProcedure"] = node.find("./scheduled-procedure").text
    if to_database["PrimaryProcedure"]:
        to_database["PrimaryProcedure"] = to_database["PrimaryProcedure"].replace("\n", " ")
    try:
        to_database["Facility"]:str = node.find("./operating-room/location/name").text
    except AttributeError:
        pass
    try:
        to_database["Room"]:str = node.find("./operating-room/sysid").text
    except AttributeError:
        pass
    to_database["ASAScore"] = node.find("./asa-classification/class").text
    positions = node.findall("./case-items/section/group")
    for group in positions:
        if group.attrib["sys-label"] == "Position":
            pos = group.findall("./case-item/associated-value-sets/associated-value-set/associated-codes/associated-code/name")
            if pos:
                to_database["SurgeryLocation1"] = pos[0].text
            if len(pos) > 1:
                to_database["SurgeryLocation2"] = pos[1].text
    surg_request = node.findall(".//*value")
    for item in surg_request:
        if item.text and re.match(r'.*surg.[ ]+request.*', item.text):
            to_database["SurgeonRequestedBlock"] = 1
        if item.text and re.match(r'.*Post-op[ ]+Pain[ ]+Mgmt.*', item.text):
            to_database["PainBlock"] = 1

    emergency:str = node.find("emergency").text
    if emergency == "Yes":
        to_database["Emergency"] = 1

    return to_database