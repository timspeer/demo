'''views'''
from datetime import datetime
import subprocess
import sqlalchemy
import dateutil.relativedelta
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import resolve
from django.views.decorators.csrf import csrf_exempt

#New method
def reconcile(client, request, query, in_phi=False):
    '''template'''
    date = datetime.now().strftime("%Y-%m-%d_%H%M")
    engine = sqlalchemy.create_engine('mssql+pymssql://#REMOVED#', isolation_level="READ UNCOMMITTED")
    conn = engine.connect()
    statement = [
        query,
        "FROM SMI_Tools.dbo.Reconcile",
        "WHERE Client = :client AND DOS > Convert(datetime, DateAdd(month, -3, Convert(date, GetDate())))",
        "ORDER BY DOS"
        ]
    if not in_phi:
        statement.insert(3, "AND InPHI = 0")
    text = sqlalchemy.text(" ".join(statement))
    query = conn.execute(text, client=client, in_phi=in_phi)
    in_phi = [dict(item) for item in query.fetchall()]
    results = {
        "in_phi" : in_phi,
        "partial" : f"reconcile/partials/{client}.html",
        "excel" : f"{client.upper()}_{date} Report.csv",
        "client" : client
        }
    return render(request, 'reconcile/reconcile_index.html', results)

def remove(request):
    '''template'''
    url = request.build_absolute_uri()
    id_ = url.split("/")[-2]
    engine = sqlalchemy.create_engine('mssql+pymssql://#REMOVED#', isolation_level="READ UNCOMMITTED")
    conn = engine.connect()
    statement = [
        "UPDATE SMI_Tools.dbo.Reconcile",
        "SET InPHI = 1",
        "WHERE ID = :id",
        ]
    text = sqlalchemy.text(" ".join(statement))
    conn.execute(text, id=id_)
    return HttpResponse('')

def undo(request):
    '''template'''
    url = request.build_absolute_uri()
    id_ = url.split("/")[-2]
    engine = sqlalchemy.create_engine('mssql+pymssql://#REMOVED#', isolation_level="READ UNCOMMITTED")
    conn = engine.connect()
    statement = [
        "UPDATE SMI_Tools.dbo.Reconcile",
        "SET InPHI = 0",
        "WHERE ID = :id",
        ]
    text = sqlalchemy.text(" ".join(statement))
    conn.execute(text, id=id_)
    conn.close()
    return HttpResponse('')

def common_index(client, request, query, in_phi=" AND IN_PHI = 0"):
    '''template'''
    engine = sqlalchemy.create_engine('mssql+pymssql://#REMOVED#', isolation_level="READ UNCOMMITTED")
    conn = engine.connect()
    statement = [
        query,
        "FROM [SMI_Schedules].[dbo].[PATH_TO_PHI]",
        f"WHERE CLIENT = '{client}' AND DOS > Convert(datetime, DateAdd(month, -3, Convert(date, GetDate()))){in_phi}",
        "ORDER BY DOS"
        ]
    query = conn.execute(" ".join(statement))
    in_phi = [list(item) for item in query.fetchall()]
    results = {
        "in_phi" : in_phi,
        }
    conn.close()
    return render(request, f'reconcile/{client}.html', results)

def refresh_content(request):
    '''refresh content'''
    client = request.build_absolute_uri().split("/")[-3]
    subprocess.Popen(["python", fr'\\smi4\DATA IT\Git\Path to PHI\{client}\{client}_run.pyw', 'Quick'])
    results = {
        "client" : client
    }
    return render(request, 'reconcile/complete.html', results)

#ANSA
def ansa_reconcile(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, BillingSlip, PDF, Schedule, CSV, InPHI, ID"
    return reconcile('ansa', request, query)

def ansa_show_in_phi(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, BillingSlip, PDF, Schedule, CSV, InPHI, ID"
    return reconcile('ansa', request, query, in_phi=True)

#BELL
def bell_reconcile(request):
    '''request'''
    query = "SELECT Client, Location, Facility, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('bell', request, query)

def bell_show_in_phi(request):
    '''request'''
    query = "SELECT Client, Location, Facility, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('bell', request, query, in_phi=True)

#BLDR
def bldr_reconcile(request):
    '''request'''
    query = "SELECT Client, MRN, DOS, CSN, LName, FName, Location, Schedule, PDF, BillingSlip, CSV, InPHI, ID"
    return reconcile('bldr', request, query)

def bldr_show_in_phi(request):
    '''request'''
    query = "SELECT Client, MRN, DOS, CSN, LName, FName, Location, Schedule, PDF, BillingSlip, CSV, InPHI, ID"
    return reconcile('bldr', request, query, in_phi=True)

#GVAA
def gvaa_reconcile(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, BillingSlip, PDF, Schedule, InPHI, ID"
    return reconcile('gvaa', request, query)

def gvaa_show_in_phi(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, BillingSlip, PDF, Schedule, InPHI, ID"
    return reconcile('gvaa', request, query, in_phi=True)

#MTRX
def mtrx_reconcile(request):
    '''request'''
    query = "SELECT Client, MRN, DOS, LName, FName, PDF, Schedule, BillingSlip, InEncounter, Location, CSN, InPHI, ID"
    return reconcile('mtrx', request, query)

def mtrx_show_in_phi(request):
    '''request'''
    query = "SELECT Client, MRN, DOS, LName, FName, PDF, Schedule, BillingSlip, InEncounter, Location, CSN, InPHI, ID"
    return reconcile('mtrx', request, query, in_phi=True)
#NRAC
def nrac_reconcile(request):
    '''request'''
    query = "SELECT Client, MRN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('nrac', request, query)

def nrac_show_in_phi(request):
    '''request'''
    query = "SELECT Client, MRN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('nrac', request, query, in_phi=True)

#OLYY
def olyy_reconcile(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('olyy', request, query)

def olyy_show_in_phi(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('olyy', request, query, in_phi=True)

#PACE
def pace_index(request):
    '''request'''
    query = "SELECT CLIENT, MRN, DOS, LAST_NAME, FIRST_NAME, LOC, IN_PHI"
    return common_index('pace', request, query)

def pace_show_in_phi(request):
    '''request'''
    query = "SELECT CLIENT, MRN, DOS, LAST_NAME, FIRST_NAME, LOC, IN_PHI"
    return common_index('pace', request, query, "")

#PCFC
def pcfc_reconcile(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('pcfc', request, query)

def pcfc_show_in_phi(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('pcfc', request, query, in_phi=True)

#RENO
def reno_reconcile(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('reno', request, query)

def reno_show_in_phi(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('reno', request, query, in_phi=True)

#RETA
def reta_reconcile(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('reta', request, query)

def reta_show_in_phi(request):
    '''request'''
    query = "SELECT Client, Location, MRN, CSN, DOS, LName, FName, PDF, Schedule, InPHI, ID"
    return reconcile('reta', request, query, in_phi=True)

#VALL
def vall_index(request):
    '''request'''
    query = "SELECT CLIENT, MRN, DOS, LAST_NAME, FIRST_NAME, FILENAME, IN_PHI"
    return common_index('vall', request, query)

def vall_show_in_phi(request):
    '''request'''
    query = "SELECT CLIENT, MRN, DOS, LAST_NAME, FIRST_NAME, FILENAME, IN_PHI"
    return common_index('vall', request, query, "")

def test():
    '''template'''
    engine = sqlalchemy.create_engine('mssql+pymssql://#REMOVED#', isolation_level="READ UNCOMMITTED")
    conn = engine.connect()
    query = "SELECT CLIENT, MRN, DOS, LAST_NAME, FIRST_NAME, FILENAME, SCHEDULE, IN_PHI, ID"
    statement = [
        query,
        "FROM [SMI_Schedules].[dbo].[PATH_TO_PHI]",
        f"WHERE CLIENT = 'NRAC' AND DOS > Convert(datetime, DateAdd(month, -2, Convert(date, GetDate()))) AND IN_PHI = 0",
        "ORDER BY DOS"
        ]
    query = conn.execute(" ".join(statement))
    in_phi = [dict(item) for item in query.fetchall()]
    print(in_phi)

if __name__ == "__main__":
    test()
