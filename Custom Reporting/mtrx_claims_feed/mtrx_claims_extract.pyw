'''creates csv for mtrx'''
import sqlalchemy
import pandas
from datetime import datetime
from collections import OrderedDict
import paramiko
import sys
import os
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', "Globals")))
from send_email import send_email
from password_encryption import get_password

def from_sql():
    '''pulls data from sql'''
    engine = sqlalchemy.create_engine('mssql+pymssql://#REMOVED#')
    conn = engine.connect()
    statement = [
        "USE #REMOVED#",
        "SELECT",
        "ClaimNumber as claimid,",
        "'' as '2',",
        "Provider.NPI as renderingphynpi,",
        "'' as '4','' as '5',",
        "CONVERT(varchar(8), ServiceLine.ServiceDtFrom, 112) as servicefromdate,",
        "CONVERT(varchar(8), ServiceLine.ServiceDtTo, 112) as servicetodate,",
        "InsPayer.Name as payername,",
        "HealthCareFacility.Name as placeofservice,",
        "CoverageSet.SubscriberNum as subscriberid,",
        "Per.LastName as subscriberlastname,",
        "Per.FirstName as subscriberfirstname,",
        "'' as '13',",
        "Per.Gender as subscribergender,",
        "CONVERT(varchar(8), Per.BirthDt, 112) as subscriberdob,",
        "'' as '16','' as '17','' as '18','' as '19','' as '20','' as '21',",
        "Person.LastName as patientlastname,",
        "Person.FirstName as patientfirstname,",
        "'' as '24',",
        "Person.Gender as patientgender,",
        "CONVERT(varchar(8), Person.BirthDt, 112) as patientdob,",
        "'' as '27','' as '28','' as '29','' as '30','' as '31','' as '32','' as '33',",
        "ICDMaster.Code as diagnostic01,",
        "'' as 'diagnostic02','' as 'diagnostic03','' as 'diagnostic04','' as 'diagnostic05','' as 'diagnostic06','' as 'diagnostic07',",
        "'' as 'diagnostic08','' as 'diagnostic09','' as 'diagnostic10','' as diagnostic11,'' as 'diagnostic12',",
        "ServiceLine.Code as cpt01,",
        "'' as '47','' as 'cpt02','' as '49','' as 'cpt03','' as '51','' as 'cpt04','' as '53','' as 'cpt05','' as '55','' as 'cpt06','' as '57','' as 'cpt07',",
        "'' as '59','' as 'cpt08','' as '61','' as 'cpt09','' as '63','' as 'cpt10','' as '65','' as 'cpt11','' as '67','' as 'cpt12','' as '69'",
        "FROM Claim",
        "INNER JOIN Incident",
        "ON Claim.IncidentID = Incident.ID",
        "INNER JOIN Provider",
        "ON Incident.ProvOrgID = Provider.ID",
        "INNER JOIN InsPlan",
        "ON InsPlan.ID = Claim.PlanID",
        "INNER JOIN InsPayer",
        "ON InsPlan.PayerID = InsPayer.ID",
        "INNER JOIN Person",
        "ON Incident.PatientID = Person.ID",
        "INNER JOIN HealthCareFacility",
        "ON HealthCareFacility.ID = Incident.FacilityID",
        "INNER JOIN CoverageSet",
        "ON Incident.ID = CoverageSet.IncidentID",
        "INNER JOIN ServiceLine",
        "ON Incident.ID = ServiceLine.IncidentID",
        "INNER JOIN Diagnosis",
        "ON Diagnosis.IncidentID = Incident.ID",
        "INNER JOIN ICDMaster",
        "ON Diagnosis.ICDMasterID = ICDMaster.ID",
        "INNER JOIN Person as per",
        "ON CoverageSet.PersonID = per.ID",
        "WHERE Incident.ProvOrgID = 10 AND FacilityID in (77, 75, 73, 49, 145, 50) AND CoverageSet.Rank = 1",
        "AND Claim.PrintedDt > Convert(datetime, DateAdd(day, -7, Convert(date, GetDate())))"
    ]
    statement = " ".join(statement)
    query = conn.execute(statement).fetchall()
    dataframe = []
    check = False
    for row in query:
        check = False
        for item in dataframe:
            if row["claimid"] == item["claimid"]:
                cpt_list = []
                dx_list = []
                for num in range(1,13):
                    cpt_list.append(item[f"cpt{str(num).zfill(2)}"])
                    dx_list.append(item[f"diagnostic{str(num).zfill(2)}"])
                cpt_list = [item_ for item_ in cpt_list if item_]
                cpt_list.append(row["cpt01"])
                cpt_list = list(dict.fromkeys(cpt_list))
                for idx, cpt in enumerate(cpt_list):
                    item[f"cpt{str(idx+1).zfill(2)}"] = cpt
                dx_list = [item_ for item_ in dx_list if item_]
                dx_list.append(row["diagnostic01"])
                dx_list = list(dict.fromkeys(dx_list))
                for idx, dx in enumerate(dx_list):
                    item[f"diagnostic{str(idx+1).zfill(2)}"] = dx
                check = True
        if check:
            continue
        dataframe.append(OrderedDict(row))
    for item in dataframe:
        if item["placeofservice"] == "Comprehensive Procedure Center":
            item["placeofservice"] = "Evergreen Hospital Medical Center"
        if item["payername"] == "Blue Cross / Blue Shield 1":
            item["payername"] = "Premera Blue Cross / Blue Shield"
        if item["payername"] == "Blue Cross / Blue Shield 2":
            item["payername"] = "Regence Blue Cross / Blue Shield"
    return dataframe

def to_csv(dframe_=None):
    '''creates the csv'''
    if not dframe_:
        dframe_ = from_sql()
    dframe = pandas.DataFrame(dframe_)
    dframe.to_csv(r'#REMOVED#',  sep='|', index=False)

def transfer():
    '''transfer the file'''
    host = "#REMOVED#"
    port = "#REMOVED#"
    transport = paramiko.Transport((host, port))
    username = "EHP-Matrix"
    password:str = get_password(username, "MTRX Claim Extract")
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    filename = f'/MTRX_Claims_Feed_{datetime.now().strftime("%Y-%m-%d")}.csv'
    sftp.put(r'#REMOVED', filename)
    transport.close()
    sftp.close()

if __name__ == "__main__":
    try:
        to_csv()
        transfer()
    except Exception as exception:
        send_email(traceback.format_exc(), "MTRX Claims Feed Traceback")
        raise exception
