'''views'''
import os
import sys
import re
from fnmatch import fnmatch
from datetime import datetime

from dateutil.relativedelta import relativedelta
from accounting.models import Providers, ProvidersFiles

sys.path.append(r'#REMOVED#')
from common import methods

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.utils.html import escape
from django.db.models.functions import Lower
from django.db import connection


def accounting_index(request):
    '''request'''
    if not request.user.username == "Accounting":
        return render(request, 'home/index.html')
    path = request.get_full_path().split("/")
    client = path[-2].upper()

    month = int((datetime.now() + relativedelta(months=-1)).strftime("%m"))
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM accounting_providersfiles WHERE month <> %s", [month])

    statement = [
        "SELECT prov.id, prov.client, prov.name, files.local_file, files.published_file, files.sharefile_folder",
        "FROM accounting_providers as prov",
        "LEFT JOIN accounting_providersfiles as files",
        "ON prov.id = files.provider_id_id",
        f"WHERE prov.client = '{client}'",
        "ORDER BY prov.name"
    ]
    query = " ".join(statement)

    providers = Providers.objects.raw(query) #This methods sanitizzes the raw query

    for idx, _ in enumerate(providers):
        if providers[idx].local_file:
            providers[idx].local_file = os.path.basename(providers[idx].local_file)

    results = {
        "partial" : f"accounting/partials/{client}.html",
        'providers' : providers
    }


    return render(request, 'accounting/accounting_index.html', results)

def ajax(request):
    '''request'''
    if not request.user.username == "Accounting":
        return render(request, 'home/index.html')
    path = request.get_full_path().split("/")
    client = path[-3].upper()

    statement = [
        "SELECT prov.id, files.local_file, files.published_file, files.sharefile_folder",
        "FROM accounting_providers as prov",
        "LEFT JOIN accounting_providersfiles as files",
        "ON prov.id = files.provider_id_id",
        f"WHERE prov.client = '{client}'",
        "ORDER BY prov.name"
    ]
    query = " ".join(statement)

    providers = Providers.objects.raw(query) #Sanitize

    prov_list:list = list()

    for item in providers:
        dict_ = {
            "id" : item.id,
        }
        if item.local_file:
            dict_['local_file'] = os.path.basename(item.local_file)
        if item.sharefile_folder:
            dict_['sharefile_folder'] = item.sharefile_folder
        if item.published_file:
            dict_['published_file'] = item.published_file
        prov_list.append(dict_)

    return JsonResponse({'providers' : prov_list})


def fill_database(request):
    '''create records'''
    if not request.user.username == "Accounting":
        return render(request, 'home/index.html')
    prev_year = (datetime.now() + relativedelta(months=-1)).strftime("%Y")
    prev_month = (datetime.now() + relativedelta(months=-1)).strftime("%m")
    month = int((datetime.now() + relativedelta(months=-1)).strftime("%m"))

    path = request.get_full_path().split("/")
    client = path[-3].upper()

    providers = Providers.objects.filter(client=client).order_by(Lower('name'))
    report_path = fr'#REMOVED#{client}\{prev_year}.{prev_month}'

    session = methods.Sharefile(client)

    name_list = session.check_folders()

    for idx, _ in enumerate(providers):
        flag = False
        if ProvidersFiles.objects.filter(provider_id=providers[idx].id).exists():
            record_ = ProvidersFiles.objects.get(provider_id=providers[idx].id)
            flag = True
            if record_.local_file and record_.sharefile_folder and record_.published_file:
                continue
        if flag:
            record = ProvidersFiles.objects.get(provider_id=providers[idx].id)
        else:
            record = ProvidersFiles(client=client, provider_id=providers[idx], month=month)
        name:str = providers[idx].name
        if name in name_list:
            record.sharefile_folder:str = name
        for root, _, files in os.walk(report_path):
            if not re.match(r'.*Ingredients.*\\Ready (?:for|to) Upload$', root):
                continue
            for pdf in files:
                pdf:str = os.path.join(root, pdf)
                if fnmatch(pdf, f"*- {name}.pdf"):
                    record.local_file:str = pdf
                    break
        match:str = session.query_file(name)

        record.published_file:str = match
        record.save()

    return HttpResponse("stop")

def create_record(request):
    '''create provider record'''
    if not request.user.username == "Accounting":
        return render(request, 'home/index.html')
    path = request.get_full_path().split("/")
    client = path[-3].upper()
    if request.method == 'POST':
        name = escape(request.POST.get('create'))
        record = Providers(client=client, name=name)
        record.save()
    return HttpResponseRedirect("/".join(path[:-2]))

def update_record(request):
    '''update provider record'''
    if not request.user.username == "Accounting":
        return render(request, 'home/index.html')
    path = request.get_full_path().split("/")
    if request.method == 'POST':
        name = escape(request.POST.get('update_name'))
        id_ = escape(request.POST.get('update_id'))
        record = Providers.objects.get(id=id_)
        record.name = name
        record.save()
    return HttpResponseRedirect("/".join(path[:-2]))

def remove_record(request):
    '''remove record'''
    if not request.user.username == "Accounting":
        return render(request, 'home/index.html')
    path = request.get_full_path().split("/")
    if request.method == 'POST':
        id_ = escape(request.POST.get('remove'))
        record = Providers.objects.get(id=id_)
        record.delete()
    return HttpResponseRedirect("/".join(path[:-2]))
    
def distribute(request):
    '''create directories'''
    if not request.user.username == "Accounting":
        return render(request, 'home/index.html')
    path = request.get_full_path().split("/")
    client = path[-3].upper()

    session = methods.Sharefile(client)

    providers = Providers.objects.filter(client=client).order_by(Lower('name'))

    provider_list:list = [[item.name, str(item.id)] for item in providers]

    prev_year = (datetime.now() + relativedelta(months=-1)).strftime("%Y")
    prev_month = (datetime.now() + relativedelta(months=-1)).strftime("%m")

    report_path = fr'#REMOVED#\{client}\{prev_year}.{prev_month}'

    for doc in provider_list:
        for root, _, files in os.walk(report_path):
            if not re.match(r'.*Ingredients.*\\Ready (?:for|to) Upload$', root):
                continue
            for pdf in files:
                pdf:str = os.path.join(root, pdf)
                if fnmatch(pdf, f"*- {doc[0]}.pdf"):
                    session.create_directories([doc[0]])
                    session.upload_file(doc[0], pdf)
                    record = ProvidersFiles.objects.get(provider_id=doc[1])
                    match:str = session.query_file(doc[0])
                    record.published_file:str = match
                    record.save()
                    break
    return HttpResponse("stop")
