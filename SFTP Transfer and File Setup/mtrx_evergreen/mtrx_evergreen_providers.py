'''extract providers'''
from datetime import datetime

def main(id_, csn, client, root):
    '''format insurances'''
    d_list = []
    node = root.find("./case/case-info")
    providers = node.findall("./assignments/assignment")
    for idx, provider in enumerate(providers):
        lname = provider.find("./assignee/user/last-name").text
        fname = provider.find("./assignee/user/first-name").text
        to_database = {
            "EncounterID" : id_,
            "CSN" : csn,
            "Client" : client,
            "Rank" : idx+1,
            "TypeProvider" : "Anesthetist",
            "StartTime" : datetime.fromisoformat(provider.find("./start-time").text),
            "RawNameProvider" : lname+', '+fname,
            "NPIProvider" : provider.find("./assignee/user/national-provider-id").text
        }
        try:
            to_database["StopTime"] = datetime.fromisoformat(provider.find("./end-time").text)
        except TypeError:
            pass
        d_list.append(to_database)
    surgeon = node.find("./surgeons/surgeon")
    try:
        to_database = {
            "EncounterID" : id_,
            "CSN" : csn,
            "Client" : client,
            "Rank" : 1,
            "TypeProvider" : "Surgeon",
            "RawNameProvider" : surgeon.find("./last-name").text+', '+surgeon.find("./first-name").text,
        }
        d_list.append(to_database)
    except AttributeError:
        pass
    resp = node.find("./provider/user")
    to_database = {
        "EncounterID" : id_,
        "CSN" : csn,
        "Client" : client,
        "Rank" : 1,
        "TypeProvider" : "Responsible Provider",
        "RawNameProvider" : resp.find("./last-name").text+', '+resp.find("./first-name").text,
        "NPIProvider" : resp.find("./national-provider-id").text
    }
    d_list.append(to_database)
    return d_list