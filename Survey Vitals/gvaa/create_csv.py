'''create the csv'''
import sqlalchemy
import pandas
from datetime import datetime
import os
import xlsxwriter

def main():
    '''main trigger'''
    engine = sqlalchemy.create_engine('mssql+pymssql://#REMOVED#')
    conn = engine.connect()
    statement = [
        "DECLARE @fromdate smalldatetime = Convert(smalldatetime, DateAdd(day, -7, Convert(date, GetDate())))",
        "DECLARE @todate smalldatetime = Convert(smalldatetime, DateAdd(day, -1, Convert(date, GetDate())))",

        "CREATE TABLE #temp_surveyvitals",
        "(",
            "[Patient First Name] VARCHAR(MAX),",
            "[Patient Last Name] VARCHAR(MAX),",
            "[Patient email] VARCHAR(MAX),",
            "[Patient Phone] VARCHAR(MAX),",
            "[Mobile Phone] VARCHAR(MAX),",
            "[Date of Service] DATETIME,",
            "[Patient DOB] DATE,",
            "[Primary Provider First Name] VARCHAR(MAX),",
            "[Primary Provider Last Name] VARCHAR(MAX),",
            "[Primary Provider NPI] VARCHAR(MAX),",
            "[Patient Zip] VARCHAR(MAX),",
            "[Secondary Provider First Name] VARCHAR(MAX),"
            "[Secondary Provider Last Name] VARCHAR(MAX),",
            "[Secondary Provider NPI] VARCHAR(MAX),",
            "[Facility Abbrev or Location Code] VARCHAR(MAX),",
            "[CPT Code] VARCHAR(MAX),",
            "[ASA Code] VARCHAR(MAX),",
            "[Case Number] VARCHAR(MAX),",
            "[Account Num] VARCHAR(MAX),",
            "[Reporting Class] VARCHAR(MAX),",
            "[Guarantor First Name] VARCHAR(MAX),",
            "[Guarantor Last Name] VARCHAR(MAX),",
            "[Guarantor Phone No.] VARCHAR(MAX),",
            "[Guarantor Email] VARCHAR(MAX),",
            "[Location Code] VARCHAR(MAX)",
        ")",

        "INSERT INTO #temp_surveyvitals",

        "EXEC #REMOVED#.spGetSurveyVital @ReleaseDtFrom = @fromdate, @ReleaseDtTo = @todate, @ProvOrgID = 30",

        "SELECT * FROM #temp_surveyvitals",
        "WHERE [CPT Code] not in ('90870') AND [CPT Code] not like '%[F|G|T]%'",
        "AND [Facility Abbrev or Location Code] in ('BDH', 'LH', 'OSCM', 'RMSC', 'SDSC')",

        "DROP TABLE #temp_surveyvitals"
    ]
    dframe = pandas.read_sql(" ".join(statement), conn, index_col=None)
    root = fr'#REMOVED#'
    if not os.path.exists(root):
        os.makedirs(root)

    date = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(root, f"Auto GVAA {date} Uploaded.xlsx")

    dframe.to_excel(filename, index=False)

if __name__ == "__main__":
    main()
