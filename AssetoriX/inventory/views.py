import csv
import io
import json
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Store, Asset

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import csv
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from .models import Asset
from .models import Store, Asset
import logging
# views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Asset
from .forms import AssetForm
from django.db.models import Q
from .models import Asset, CustodianHistory
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomPasswordChangeForm


def custom_password_change(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password changed successfully.")
            return redirect('login')
    else:
        form = CustomPasswordChangeForm()
    return render(request, 'inventory/custom_password_change.html',
                  {'form': form})


def asset_create(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:asset_list')  # Use namespace if exists
    else:
        form = AssetForm()
    return render(request, 'inventory/asset_form.html', {'form': form})


def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            return redirect('inventory:asset_list')
    else:
        form = AssetForm(instance=asset)
    return render(request, 'inventory/asset_form.html', {'form': form})


def asset_list(request):
    query = request.GET.get('q', '')  # Get search query, default empty string
    if query:
        # Filter assets by item name or serial number (example)
        assets = Asset.objects.filter(
            Q(item__icontains=query) | Q(serial_number__icontains=query))
    else:
        assets = Asset.objects.none(
        )  # Show no results if no query (or you can show all)

    return render(request, 'inventory/asset_list.html', {
        'assets': assets,
        'query': query
    })


logger = logging.getLogger(__name__)


def get_assets_by_custodian(request):
    custodian = request.GET.get('custodian')
    if not custodian:
        return JsonResponse({'assets': []})

    assets = Asset.objects.filter(current_custodian__iexact=custodian)

    asset_data = [{
        'serial_number': asset.serial_number,
        'item': asset.item,
        'model': asset.model,
        'quantity': asset.quantity,
        'working_status': asset.working_status
    } for asset in assets]
    return JsonResponse({'assets': asset_data})


from django.http import JsonResponse
from .models import Asset  # adjust if your model import is different


def get_assets_by_location(request):
    location = request.GET.get('location', 'DIYAFAH')
    if not location:
        return JsonResponse({'assets': []})

    assets = Asset.objects.filter(current_location__iexact=location)

    asset_data = [{
        'serial_number': asset.serial_number,
        'item': asset.item,
        'model': asset.model,
        'quantity': asset.quantity,
        'working_status': asset.working_status
    } for asset in assets]
    return JsonResponse({'assets': asset_data})


def index(request):
    user = request.user
    # Check if user belongs to the 'technicians' group
    if user.groups.filter(name='technicians').exists():
        return redirect(
            'inventory:index.html')  # redirect to a URL pattern named 'index'

    # Otherwise render the normal page or do something else
    return render(request, 'inventory/index.html')


@csrf_exempt
def import_data(request):
    if request.method == 'POST':
        model = request.POST.get('model')
        csv_file = request.FILES.get('csv_file')

        if not csv_file.name.endswith('.csv'):
            return JsonResponse({'error': 'Only CSV files are supported.'},
                                status=400)

        decoded = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)

        success = 0
        failed = 0

        if model == 'store':
            for idx, row in enumerate(reader, start=1):
                try:
                    Store.objects.update_or_create(code=row['code'],
                                                   defaults={
                                                       'name': row['name'],
                                                       'address':
                                                       row['address']
                                                   })
                    success += 1
                except Exception as e:
                    logger.error(f"Line {idx} - Store import failed: {e}")
                    failed += 1

        elif model == 'asset':
            for idx, row in enumerate(reader, start=1):
                try:
                    store_code = row['store'].strip()
                    if not store_code:
                        raise ValueError("Empty store code")

                    store = Store.objects.get(code=store_code)

                    Asset.objects.update_or_create(
                        serial_number=row['serial_number'],
                        defaults={
                            'item': row['item'],
                            'model': row['model'],
                            'invoice_number': row['invoice_number'],
                            'purchase_date': row['purchase_date'],
                            'current_location': row['current_location'],
                            'supplier_name': row['supplier_name'],
                            'working_status': row['working_status'],
                            'current_custodian': row['current_custodian'],
                            'warranty_end_date': row['warranty_end_date'],
                            'quantity': row.get('quantity', 1),
                            'store': store  # assuming ForeignKey to Store
                        })
                    success += 1
                except Store.DoesNotExist:
                    logger.error(
                        f"Line {idx} - Store with code '{store_code}' does not exist."
                    )
                    failed += 1
                except Exception as e:
                    logger.error(f"Line {idx} - Asset import failed: {e}")
                    failed += 1

        else:
            return JsonResponse({'error': 'Invalid model type provided.'},
                                status=400)

        return JsonResponse({'imported': success, 'failed': failed})

    return render(request, 'inventory/import_export.html')


def export_store_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stores.csv"'

    writer = csv.writer(response)
    writer.writerow(['code', 'name', 'address'])

    for store in Store.objects.all():
        writer.writerow([store.code, store.name, store.address])

    return response


def export_asset_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assets.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'serial_number', 'item', 'model', 'invoice_number', 'purchase_date',
        'current_location', 'supplier_name', 'working_status',
        'current_custodian', 'warranty_end_date', 'quantity', 'store'
    ])

    for asset in Asset.objects.all():
        writer.writerow([
            asset.serial_number, asset.item, asset.model, asset.invoice_number,
            asset.purchase_date, asset.current_location, asset.supplier_name,
            asset.working_status, asset.current_custodian,
            asset.warranty_end_date, asset.quantity,
            asset.store.code if asset.store else ''
        ])

    return response


def user_logout(request):
    logout(request)
    return redirect('inventory:login')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Group-based redirection
            if user.groups.filter(name='managers').exists():
                return redirect('inventory:index')
            elif user.groups.filter(name='technicians').exists():
                return redirect('inventory:dashboard')
            else:
                return redirect('inventory:guest')

        else:
            return render(request, 'inventory/login.html',
                          {'error': 'Invalid username or password.'})

    return render(request, 'inventory/login.html')


@login_required
def dashboard(request):
    return render(request, 'inventory/dashboard.html')


@login_required
def guest(request):
    return render(request, 'inventory/guest.html')


# Installation Form View
def installation_form(request):
    stores = Store.objects.all()
    assets = Asset.objects.filter(current_location="Out_Transit")
    return render(request, 'inventory/installation_form.html', {
        'stores': stores,
        'assets': assets
    })


# Installation Form View
def dispatch_form(request):
    stores = Store.objects.all()
    assets = Asset.objects.exclude(current_custodian="1236")
    return render(request, 'inventory/dispatch_form.html', {
        'stores': stores,
        'assets': assets
    })


# Installation Form View
def installation_ir_form(request):
    stores = Store.objects.all()
    assets = Asset.objects.exclude(current_custodian="1236")
    return render(request, 'inventory/ir_form.html', {
        'stores': stores,
        'assets': assets
    })


# Dispatch Form View
def dispatch_link_form(request):
    stores = Store.objects.all()
    assets = Asset.objects.exclude(current_custodian="1236")
    return render(request, 'inventory/dispatch_form.html', {
        'stores': stores,
        'assets': assets
    })


def search_store_wise(request):
    query = request.GET.get('q', '').strip()
    filter_by = request.GET.get('filter_by', 'location')  # Default to location
    assets = []

    if query:
        if filter_by == 'location':
            assets = Asset.objects.filter(current_custodian__icontains=query)
        elif filter_by == 'item':
            assets = Asset.objects.filter(item__icontains=query)
        elif filter_by == 'model':
            assets = Asset.objects.filter(model__icontains=query)
        elif filter_by == 'vendor':
            assets = Asset.objects.filter(supplier_name__icontains=query)
        elif filter_by == 'invoice':
            assets = Asset.objects.filter(invoice_number__icontains=query)
        elif filter_by == 'status':
            assets = Asset.objects.filter(working_status__icontains=query)

    return render(request, 'inventory/search_store_wise.html', {
        'query': query,
        'filter_by': filter_by,
        'assets': assets
    })


#Search
# AJAX Store info
def get_store_info(request):
    code = request.GET.get('code')
    try:
        store = Store.objects.get(code=code)
        return JsonResponse({'name': store.name, 'address': store.address})
    except Store.DoesNotExist:
        return JsonResponse({'error': 'Store not found'}, status=404)


# AJAX Asset info
def get_asset_info(request):
    serial = request.GET.get('serial')
    try:
        asset = Asset.objects.get(serial_number=serial)
        return JsonResponse({
            'item': asset.item,
            'model': asset.model,
            'quantity': asset.quantity
        })
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)


# Generate Installation Report PDF
@csrf_exempt
def generate_pdf(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            store_code = data.get('store_code')
            serial_numbers = data.get('serial_numbers', [])

            store = Store.objects.get(code=store_code)
            assets = []

            for serial in serial_numbers:
                try:
                    asset = Asset.objects.get(serial_number=serial)
                    asset.current_location = store.name
                    asset.current_custodian = store.code
                    asset.save()
                    assets.append(asset)
                except Asset.DoesNotExist:
                    continue

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer,
                                    pagesize=A4,
                                    rightMargin=2 * cm,
                                    leftMargin=2 * cm,
                                    topMargin=1.5 * cm,
                                    bottomMargin=1.5 * cm)
            styles = getSampleStyleSheet()
            elements = []

            # Header
            title_style = styles['Title']
            title_style.alignment = 1
            elements.append(Paragraph("IT INSTALLATION REPORT", title_style))
            elements.append(Spacer(1, 12))

            header_data = [
                [
                    f"SL NO: IR_{store.code}_Aster",
                    f"INSTALLED DATE: {datetime.now().strftime('%d-%m-%Y')}"
                ],
                ["Store Code:", f"{store.code}"],
                ["Store Name:", f"{store.name}"],
                ["Store Address:", f"{store.address}"],
                ["Ticket Number: ", "Type of installation: "],
            ]
            header_table = Table(header_data, colWidths=[5.7 * cm, 12.3 * cm])
            header_table.setStyle(
                TableStyle([
                    ('BOX', (0, 0), (-1, -1), 0.6, colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.grey),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
            elements.append(header_table)
            elements.append(Spacer(1, 10))

            # ITEMS Section
            elements.append(Paragraph("ITEMS", styles['Heading5']))
            item_table_data = [[
                "Name and \nSerial Number", "Quantity", "Invoice Number",
                "Item", "Item Status"
            ]]

            for asset in assets:
                item_table_data.append([
                    f"{asset.model}\nS/N: {asset.serial_number}",
                    asset.quantity, asset.invoice_number, asset.item,
                    asset.working_status or "N/A"
                ])

            item_table = Table(
                item_table_data,
                colWidths=[5.5 * cm, 2 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
            item_table.setStyle(
                TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.6, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
            elements.append(item_table)

            # Total count
            elements.append(Spacer(1, 6))
            elements.append(
                Paragraph(f"Total Items Count: {len(assets)}",
                          styles['Normal']))
            elements.append(Spacer(1, 12))

            # Service details
            elements.append(Paragraph("SERVICE DETAILS", styles['Heading5']))
            service_table = Table(
                [["Items Collected By: ", f"{asset.previous_custodian}"],
                 ["Items Installed By: ", f"{asset.previous_custodian}"]],
                colWidths=[7 * cm, 11 * cm])
            service_table.setStyle(
                TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                ]))
            elements.append(service_table)
            elements.append(Spacer(1, 12))

            # Store feedback
            elements.append(Paragraph("STORE FEEDBACK", styles['Heading5']))
            feedback_table = Table(
                [["Remarks:", ""], ["Name:", ""],
                 ["Date:", datetime.now().strftime('%d-%m-%Y')],
                 ["Designation:", ""], ["Signature & Seal:", ""]],
                colWidths=[7 * cm, 11 * cm],
                rowHeights=[.75 * cm, .75 * cm, .75 * cm, .75 * cm, 3 * cm])
            feedback_table.setStyle(
                TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                ]))

            elements.append(feedback_table)

            doc.build(elements)
            buffer.seek(0)
            return FileResponse(buffer,
                                as_attachment=True,
                                filename='IR_{store_code}Aster.pdf')

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


# Search Assets View
def search_assets(request):
    query = request.GET.get('q', '').strip()
    asset = None

    if query:
        asset = Asset.objects.filter(serial_number__icontains=query).first()

    return render(request, 'inventory/search.html', {
        'query': query,
        'asset': asset,
    })


# return note generation
@csrf_exempt
def generate_ir_pdf(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("You must be logged in.")

    if not request.user.groups.filter(name="technicians").exists():
        return HttpResponseForbidden("Access denied: Technicians only.")

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            store_code = data.get('store_code')
            serial_numbers = data.get('serial_numbers', [])
            statuses = data.get('statuses', [])  # ✅ Add this line

            store = Store.objects.get(code=store_code)
            assets = []

            for serial, status in zip(serial_numbers, statuses):
                try:
                    asset = Asset.objects.get(serial_number=serial)
                    asset.current_location = "In Transit"
                    asset.current_custodian = request.user.username
                    asset.working_status = status  # ✅ Correct assignment
                    asset.save()
                    assets.append(asset)
                except Asset.DoesNotExist:
                    continue

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer,
                                    pagesize=A4,
                                    rightMargin=2 * cm,
                                    leftMargin=2 * cm,
                                    topMargin=1.5 * cm,
                                    bottomMargin=1.5 * cm)
            styles = getSampleStyleSheet()
            elements = []

            # Header
            title_style = styles['Title']
            title_style.alignment = 1
            elements.append(Paragraph("IT RETURN DOCUMENT", title_style))
            elements.append(Spacer(1, 12))

            header_data = [
                [
                    f"SL NO: IT_RET_{store.code}_Aster",
                    f"Return DATE: {datetime.now().strftime('%d-%m-%Y')}"
                ],
                ["Store Code:", f"{store.code}"],
                ["Store Name:", f"{store.name}"],
                ["Store Address:", f"{store.address}"],
                ["Reason for return: ", ""],
            ]
            header_table = Table(header_data, colWidths=[7 * cm, 11 * cm])
            header_table.setStyle(
                TableStyle([
                    ('BOX', (0, 0), (-1, -1), 0.6, colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.grey),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
            elements.append(header_table)
            elements.append(Spacer(1, 10))

            # ITEMS Section
            elements.append(Paragraph("ITEMS", styles['Heading4']))
            item_table_data = [[
                "Name and \nSerial Number", "Qty", "Invoice Number", "Item",
                "Remarks"
            ]]

            for asset in assets:
                item_table_data.append([
                    f"{asset.model}\nS/N: {asset.serial_number}",
                    asset.quantity,
                    asset.invoice_number,
                    asset.item,
                ])

            item_table = Table(
                item_table_data,
                colWidths=[4.8 * cm, .95 * cm, 3.35 * cm, 3.4 * cm, 5.5 * cm])
            item_table.setStyle(
                TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.6, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
            elements.append(item_table)

            # Total count
            elements.append(Spacer(1, 6))
            elements.append(
                Paragraph(f"Total Items Count: {len(assets)}",
                          styles['Normal']))
            elements.append(Spacer(1, 12))

            # Service details
            elements.append(Paragraph("SERVICE DETAILS", styles['Heading4']))
            service_table = Table(
                [["Items Collected By: ", f"{asset.current_custodian}"],
                 ["Items Returned By: ", f"{asset.current_custodian}"]],
                colWidths=[7 * cm, 11 * cm])
            service_table.setStyle(
                TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                ]))
            elements.append(service_table)
            elements.append(Spacer(1, 12))

            # Store feedback
            elements.append(Paragraph("STORE FEEDBACK", styles['Heading4']))
            feedback_table = Table(
                [["Remarks:", ""], ["Name:", ""],
                 ["Date:", datetime.now().strftime('%d-%m-%Y')],
                 ["Designation:", ""], ["Signature & Seal:", ""]],
                colWidths=[7 * cm, 11 * cm],
                rowHeights=[.75 * cm, .75 * cm, .75 * cm, .75 * cm, 3 * cm])
            feedback_table.setStyle(
                TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                ]))

            elements.append(feedback_table)

            doc.build(elements)
            buffer.seek(0)
            return FileResponse(buffer,
                                as_attachment=True,
                                filename='IT_RE_{store_code}Aster.pdf')

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


#Dispatch note generation
@csrf_exempt
def dispatch_pdf(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("You must be logged in.")

    if not request.user.groups.filter(name="managers").exists():
        return HttpResponseForbidden("Access denied: managers only.")

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            store_code = data.get('store_code')
            serial_numbers = data.get('serial_numbers', [])
            dispatcher = data.get('dispatcher')  # Get dispatcher from request

            store = Store.objects.get(code=store_code)
            assets = []

            for serial in serial_numbers:
                try:
                    asset = Asset.objects.get(serial_number=serial)
                    asset.current_location = "Out_Transit"
                    asset.current_custodian = dispatcher  # Save dispatcher value here
                    asset.save()
                    assets.append(asset)
                except Asset.DoesNotExist:
                    continue

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer,
                                    pagesize=A4,
                                    rightMargin=2 * cm,
                                    leftMargin=2 * cm,
                                    topMargin=1.5 * cm,
                                    bottomMargin=1.5 * cm)
            styles = getSampleStyleSheet()
            elements = []

            # Header
            title_style = styles['Title']
            title_style.alignment = 1
            elements.append(Paragraph("IT DISPATCH DOCUMENT", title_style))
            elements.append(Spacer(1, 12))

            header_data = [
                [
                    f"SL NO: IT_DIS_{store.code}_Aster",
                    f"DISPATCH DATE: {datetime.now().strftime('%d-%m-%Y')} & Ticket no:"
                ],
                [f"Dispatch Store:", f"{store.name}"],
                ["Store Address:", f"{store.address}"],
                ["Store Code", f"{store.code}"],
                ["Instruction From:", ""],
            ]
            header_table = Table(header_data, colWidths=[5.7 * cm, 12.3 * cm])
            header_table.setStyle(
                TableStyle([
                    ('BOX', (0, 0), (-1, -1), 0.6, colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.grey),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
            elements.append(header_table)
            elements.append(Spacer(1, 10))

            # ITEMS Section
            elements.append(Paragraph("ITEMS", styles['Heading5']))
            item_table_data = [[
                "Name and \nSerial Number", "Qty", "Invoice Number", "Item",
                "Remarks"
            ]]

            for asset in assets:
                item_table_data.append([
                    f"{asset.model}\nS/N: {asset.serial_number}",
                    asset.quantity,
                    asset.invoice_number,
                    asset.item,
                ])

            item_table = Table(
                item_table_data,
                colWidths=[4.8 * cm, .95 * cm, 3.35 * cm, 3.4 * cm, 5.5 * cm])
            item_table.setStyle(
                TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.6, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
            elements.append(item_table)

            # Total count
            elements.append(Spacer(1, 6))
            elements.append(
                Paragraph(f"Total Items Count: {len(assets)}",
                          styles['Normal']))
            elements.append(Spacer(1, 12))

            # Service details
            elements.append(Paragraph("SERVICE DETAILS", styles['Heading5']))
            service_table = Table(
                [["Items dispatched from: ", f"{asset.previous_custodian}"],
                 ["Items Collected By:", f"{asset.current_custodian}"]],
                colWidths=[7 * cm, 11 * cm])
            service_table.setStyle(
                TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                ]))
            elements.append(service_table)
            elements.append(Spacer(1, 12))

            # Store feedback
            elements.append(Paragraph("STORE FEEDBACK", styles['Heading5']))
            feedback_table = Table(
                [["Remarks:", ""], ["Name:", ""],
                 ["Date:", datetime.now().strftime('%d-%m-%Y')],
                 ["Designation:", ""], ["Signature & Seal:", ""]],
                colWidths=[7 * cm, 11 * cm],
                rowHeights=[.75 * cm, .75 * cm, .75 * cm, .75 * cm, 3 * cm])
            feedback_table.setStyle(
                TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                ]))

            elements.append(feedback_table)

            doc.build(elements)
            buffer.seek(0)
            return FileResponse(buffer,
                                as_attachment=True,
                                filename='IT_RE_{store_code}Aster.pdf')

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def all_assets_view(request):
    assets = Asset.objects.all()
    return render(request, 'inventory/all_assets.html', {'assets': assets})


@csrf_exempt
def update_custodian(request):
    serial_number = request.POST.get('serial_number')
    new_custodian = request.POST.get(
        'new_custodian')  # or from authenticated user

    asset = Asset.objects.get(serial_number=serial_number)

    if asset.current_custodian != new_custodian:
        asset.previous_custodian = asset.current_custodian  # Save current as previous
        asset.current_custodian = new_custodian  # Now update to new
        asset.save()


def update_location(request):
    asset = Asset.objects.get(serial_number=serial_number)

    # Save current location as previous before updating
    asset.previous_location = asset.current_location
    asset.current_location = new_location  # from request or logic

    asset.save()


@login_required
def transit_update_view(request):
    return render(request, 'inventory/transit_update.html')


@csrf_exempt
def get_transit_asset(request):
    if request.method == 'GET':
        serial = request.GET.get('serial')
        if not serial:
            return JsonResponse({'error': 'serial parameter missing'},
                                status=400)
        try:
            asset = Asset.objects.get(serial_number=serial,
                                      current_location="In Transit")
            return JsonResponse({
                'serial_number': asset.serial_number,
                'current_location': asset.current_location,
                'working_status': asset.working_status
            })
        except Asset.DoesNotExist:
            return JsonResponse({'error': 'No matching asset found'},
                                status=404)

    elif request.method == 'POST':
        if request.content_type != 'application/json':
            return JsonResponse(
                {'error': 'Content-Type must be application/json'}, status=400)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        serial = data.get('serial_number')
        new_location = data.get('new_location')  # corrected key here
        new_status = data.get('working_status')  # corrected key here

        if not all([serial, new_location, new_status]):
            return JsonResponse(
                {'error': 'Missing one or more required fields'}, status=400)

        try:
            asset = Asset.objects.get(serial_number=serial,
                                      current_location="In Transit")
        except Asset.DoesNotExist:
            return JsonResponse({'error': 'Asset not found or not in transit'},
                                status=404)

        asset.current_location = new_location
        asset.working_status = new_status
        asset.location_last_updated = timezone.now()
        asset.current_custodian = request.user.username
        asset.save()

        return JsonResponse({'message': 'Asset updated successfully'})

    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
