'''PCFC CHI Reconcile'''
import os
import sys

import pcfc_chi_csvs
import pcfc_chi_billing_slips

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import methods

def main(facility:str) -> None:
    '''main function'''
    try:
        reconcile:object = methods.Reconcile(facility)

        text:str = sql()
        with reconcile.engine.connect() as conn:
            conn.execute(
                text,
                client=reconcile.client['client'],
                location=reconcile.client['location']
                )

        pcfc_chi_csvs.main(facility)
        pcfc_chi_billing_slips.main(facility)
        reconcile.check_in_phi_on_mrn()
    except Exception as exception:
        methods.send_email(methods.traceback.format_exc(), __doc__)
        raise exception

def sql() -> str:
    '''create update string'''
    statement:list = [
        "UPDATE #REMOVED#",

        "SET CSN = encounter.CSN,",
        "DOB = encounter.DOB,",
        "InEncounter = 1,",
        "PDF = encounter.Filename,",
        "LName = encounter.LName,",
        "FName = encounter.FName",

        "FROM #REMOVED#",
        "INNER JOIN #REMOVED#",
        "ON Reconcile.DOS = Encounter.DOS ",
        "AND Reconcile.Client = Encounter.Client ",
        "AND Encounter.Location = Reconcile.Location ",

        "AND (Reconcile.MRN = Encounter.MRN OR ",
        "(Reconcile.LName = Encounter.LName ",
        "AND Reconcile.FName = Encounter.FName))",

        "WHERE Reconcile.InEncounter = 0 ",
        "AND Reconcile.Client = :client ",
        "AND Reconcile.Location = :location",

        "INSERT INTO #REMOVED# (",
            "Client,",
            "Location,",
            "Facility,",
            "DOS,",
            "CSN,",
            "MRN,",
            "LName,",
            "FName,",
            "DOB,",
            "InEncounter,",
            "PDF",
            ")",
        "SELECT",
            "encounter.Client,",
            "encounter.Location,",
            "encounter.Facility,",
            "encounter.DOS,",
            "encounter.CSN,",
            "encounter.MRN,",
            "encounter.LName,",
            "encounter.FName,",
            "encounter.DOB,",
            "1,",
            "encounter.Filename",
        "FROM #REMOVED# as encounter",
        "LEFT JOIN #REMOVED#",
        "ON encounter.CSN = Reconcile.CSN",
        "WHERE Reconcile.CSN is NULL ",
        "AND encounter.Client = :client and encounter.Location = :location",
        "AND Encounter.Facility <> 'N/A'"
    ]
    query_string:str = methods.sqlalchemy.text(" ".join(statement)) #Sanitized
    return query_string

if __name__ == "__main__":
    main("PCFC_CHI")