from django.urls import path, include
from . import views
from django.views.generic import RedirectView  # ← Required for redirect
from django.contrib.auth import views as auth_views

app_name = 'inventory'

urlpatterns = [
    path('installation-form/',
         views.installation_form,
         name='installation_form'),
    path('get_store_info/', views.get_store_info, name='get_store_info'),
    path('get_asset_info/', views.get_asset_info, name='get_asset_info'),
    path('generate_pdf/', views.generate_pdf, name='generate_pdf'),
    path('search/', views.search_assets, name='search_assets'),
    path('login/', views.user_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('guest/', views.guest, name='guest'),
    path('search_store_wise/',
         views.search_store_wise,
         name='search_store_wise'),
    path('logout/', views.user_logout,
         name='logout'),  # ← Only one logout route
    path('import_export/', views.import_data, name='import_export'),
    path('export_store_csv/', views.export_store_csv, name='export_store_csv'),
    path('export_asset_csv/', views.export_asset_csv, name='export_asset_csv'),
    path('installation_ir_form/',
         views.installation_ir_form,
         name='installation_ir_form'),
    path('generate_ir_pdf/', views.generate_ir_pdf, name='generate_ir_pdf'),
    path('dispatch_pdf/', views.dispatch_pdf, name='dispatch_pdf'),
    path('index/', views.index, name='index'),

    # Redirect empty /inventory/ to login
    path('', RedirectView.as_view(url='/inventory/login/', permanent=False)),
    path('get_assets_by_custodian/',
         views.get_assets_by_custodian,
         name='get_assets_by_custodian'),
    path('dispatch_form/', views.dispatch_form, name='dispatch_form'),
    path('get_assets_by_location/',
         views.get_assets_by_location,
         name='get_assets_by_location'),
    path('dispatch_link_form/',
         views.dispatch_link_form,
         name='dispatch_link_form'),
    path('all-assets/', views.all_assets_view, name='all_assets'),
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/add/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/edit/', views.asset_update, name='asset_update'),
    path('transit_update/', views.transit_update_view, name='transit_update'),
    path('get_transit_asset/',
         views.get_transit_asset,
         name='get_transit_asset'),
    path('password_change/',
         auth_views.PasswordChangeView.as_view(
             template_name='inventory/password_change.html'),
         name='password_change'),
    path('password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='inventory/password_change_done.html'),
         name='password_change_done'),
    path('custom_password_change/',
         views.custom_password_change,
         name='custom_password_change'),
]
