'''urls'''
from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path(r'[a-z]{4}/rerun/$', views.refresh_content, name='refresh'),
    re_path(r'^remove/[0-9]+/$', views.remove, name="remove"),
    re_path(r'^undo/[0-9]+/$', views.undo, name="undo"),

    #ANSA
    path('ansa/', views.ansa_reconcile, name="ansa"),
    path('ansa/in_phi/', views.ansa_show_in_phi, name='ansa_show_in_phi'),

    #BELL
    path('bell/', views.bell_reconcile, name="bell"),
    path('bell/in_phi/', views.bell_show_in_phi, name='bell_show_in_phi'),

    #BLDR
    path('bldr/', views.bldr_reconcile, name="bldr"),
    path('bldr/in_phi/', views.bldr_show_in_phi, name='bldr_show_in_phi'),

    #GVAA
    path('gvaa/', views.gvaa_reconcile, name="gvaa"),
    path('gvaa/in_phi/', views.gvaa_show_in_phi, name='gvaa_show_in_phi'),

    #MTRX
    path('mtrx/', views.mtrx_reconcile, name="mtrx"),
    path('mtrx/in_phi/', views.mtrx_show_in_phi, name='mtrx_show_in_phi'),
                                     
    #NRAC
    path('nrac/', views.nrac_reconcile, name="nrac"),
    path('nrac/in_phi/', views.nrac_show_in_phi, name='nrac_show_in_phi'),

    #OLYY
    path('olyy/', views.olyy_reconcile, name="olyy"),
    path('olyy/in_phi/', views.olyy_show_in_phi, name='olyy_show_in_phi'),

    path('pace/', views.pace_index, name="pace"),
    path('pace/in_phi/', views.pace_show_in_phi, name='pace_show_in_phi'),

    #PCFC
    re_path(r'^pcfc/$', views.pcfc_reconcile, name="pcfc"),
    re_path(r'^pcfc/in_phi/$', views.pcfc_show_in_phi, name='pcfc_show_in_phi'),

    #RENO
    re_path(r'^reno/$', views.reno_reconcile, name="reno"),
    re_path(r'^reno/in_phi/$', views.reno_show_in_phi, name='reno_show_in_phi'),

    #RETA
    re_path(r'^reta/$', views.reta_reconcile, name="reta"),
    re_path(r'^reta/in_phi/$', views.reta_show_in_phi, name='reta_show_in_phi'),

    path('vall/', views.vall_index, name="vall"),
    path('vall/in_phi/', views.vall_show_in_phi, name='vall_show_in_phi'),

]
