'''parse codes'''
import re

def main(id_, csn, root):
    '''format codes'''
    d_list = []
    node = root.find("./case/case-info")
    blocks = node.findall(".//*[@sys-label='Block']")
    usg = node.find(".//*[@sys-label='Ultrasound Guided']")
    cath = node.find(".//*[@sys-label='Post-Nerve Catheter Phone Follow Up']")
    if usg:
        to_database = {
            "EncounterID" : id_,
            "CSN" : csn,
            "Rank" : 1,
            "Type" : "Technique",
            "Code" : usg.find(".//code").text,
            "Description" : "Ultrasound Guided"
        }
        d_list.append(to_database)
    for idx, block in enumerate(blocks):
        try:
            to_database = {
                "EncounterID" : id_,
                "CSN" : csn,
                "Rank" : idx+1,
                "Type" : "Block",
                "Code" : block.find(".//code").text,
                "Description" : block.find(".//associated-code/name").text,
                "Value" : block.find(".//value").text
            }
            d_list.append(to_database)
        except AttributeError:
            pass
        try:
            to_database = {
                "EncounterID" : id_,
                "CSN" : csn,
                "Rank" : idx+1,
                "Type" : "Event",
                "Code" : block.findall(".//associated-code/code")[1].text,
                "Description" : block.findall(".//associated-code/name")[1].text
            }
            d_list.append(to_database)
        except (AttributeError, IndexError):
            pass
    cpts = node.findall(".//cpts/cpt")
    for idx, cpt in enumerate(cpts):
        to_database = {
            "EncounterID" : id_,
            "CSN" : csn,
            "Rank" : idx+1,
            "Type" : "CPT",
            "Code" : cpt.attrib["code"],
            "Description" : cpt.find(".//name").text+' '+cpt.find(".//description").text
        }
        d_list.append(to_database)
    dx = node.find("./scheduled-diagnosis").text
    if dx:
        codes = re.findall(r'[A-Z]{1}\d+.[^ \)A-Z]+', dx)
        if not codes:
            to_database = {
                "EncounterID" : id_,
                "CSN" : csn,
                "Rank" : 1,
                "Type" : "DX",
                "Code" : '',
                "Description" : dx
            }
            d_list.append(to_database)
        else:
            for idx, item in enumerate(codes):
                description:str = re.findall(fr'.*(?=[\(]?{item})', dx)[0].strip()
                dx:str = re.sub(fr'.*\({item}\)', '', dx).strip()
                to_database = {
                    "EncounterID" : id_,
                    "CSN" : csn,
                    "Rank" : idx+1,
                    "Type" : "DX",
                    "Code" : item,
                    "Description" : description
                }
                d_list.append(to_database)
    hx_list = node.findall('./medical-history-items//associated-code')
    temp_list = []
    for hx in hx_list:
        code = hx.find(".//code").text
        description = hx.find(".//name").text
        value = hx.find(".//value").text
        if not re.match(r'\d+', code):
            continue
        temp_list.append((code, description, value))
    temp_list = list(dict.fromkeys(temp_list))
    num:int = int()
    for idx, item in enumerate(temp_list):
        if item[2] == 'No':
            num =+ 1
            continue
        try:
            value:str = item[2].replace("\n", ' ')
        except AttributeError:
            value:str = str()
        to_database = {
            "EncounterID" : id_,
            "CSN" : csn,
            "Rank" : idx+1-num,
            "Type" : "HX",
            "Code" : item[0],
            "Description" : item[1],
            "Value" : value
        }
        d_list.append(to_database)
    if cath:
        pain_increase = node.find(".//*[@sys-label='Pain Increased after Catheter Removal']/value")
        if pain_increase:
            pain_increase = pain_increase.text
        else:
            pain_increase = "No Data"
        sensory_motor = node.find(".//*[@sys-label='Sensory and Motor Returned to Normal']/value")
        if sensory_motor:
            sensory_motor = sensory_motor.text
        else:
            sensory_motor = "No Data"
        nerve_again = node.find(".//*[@sys-label='Would the Patient Want a Nerve Catheter Again']/value")
        if nerve_again:
            nerve_again = nerve_again.text
        else:
            nerve_again = "No Data"
        comment = node.find(".//*[@sys-label='Comments']/value")
        if comment:
            comment = comment.text
        else:
            comment = 'None'
        list_ = [
            f'Pain Increased after Catheter Removal:{pain_increase}',
            f'Sensory and Motor Returned to Normal:{sensory_motor}',
            f'Would the Patient Want a Nerve Catheter Again:{nerve_again}',
            f'Comments:{comment}'
        ]
        to_database = {
            "EncounterID" : id_,
            "CSN" : csn,
            "Rank" : 1,
            "Type" : "Qgenda",
            "Description" : "|".join(list_)
        }
        d_list.append(to_database)
    return d_list