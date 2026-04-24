from django.template import loader
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from .models import PerfumeTransaction,PerfumePicture,UserProfile
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from .models import Fragrance
import json
from . import Transactions
from .forms import PerfumeTransactionForm
from django.http import JsonResponse
from datetime import date,datetime
from . import GlobalParameters
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from . import Tools


def monthly_financial(request):
    # Get distinct year-months from all dates
    purchase_dates = PerfumeTransaction.objects.dates('purchase_date', 'month')
    sale_dates = PerfumeTransaction.objects.dates('sale_date', 'month')
    all_dates = list(set(purchase_dates) | set(sale_dates))
    all_dates.sort(reverse=True)

    year_months = [date.strftime('%Y-%m') for date in all_dates]

    return render(request, 'monthly_financial.html', {
        'year_months': year_months
    })

@staff_member_required
def get_monthly_transactions(request):
    year_month = request.GET.get('year_month')
    year, month = year_month.split('-')

    purchases = PerfumeTransaction.objects.filter(
        purchase_date__year=year,
        purchase_date__month=month
    )

    sales = PerfumeTransaction.objects.filter(
        sale_date__year=year,
        sale_date__month=month
    )

    return JsonResponse({
        'purchases': list(purchases.values()),
        'sales': list(sales.values())
    })

def start_add_transaction(request):
    return render(request, 'add_transaction.html')


@csrf_exempt
@staff_member_required
def add_transaction(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            exch_rate=GlobalParameters.EXCHANGE_RATES[data['currency']]
            price_euro=float(data['price'])/exch_rate
            transaction = PerfumeTransaction(
                perfumer=data['perfumer'],
                fragrance=data['fragrance'],
                origin=data['origin'],
                bottle=data['bottle'],
                package=data['package'],
                location=data['location'],
                price=float(data['price']),
                purchase_currency=data['currency'],
                purchase_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                discount=0.,
                vat_back=0.,
                purch_exch_rate=exch_rate,
                purchase_price_euro=price_euro,
                listed_price_ruble=round(price_euro*(1.+GlobalParameters.TARGET_PREMIUM)*GlobalParameters.EXCHANGE_RATES['RUB'],-3),
                listed_price_aed=round(price_euro*(1.+GlobalParameters.TARGET_PREMIUM)*GlobalParameters.EXCHANGE_RATES['AED'],-1)

            )
            transaction.save()
            return JsonResponse({
                'status': 'success',
                'message': f'{data["perfumer"]} - {data["fragrance"]} bought for {price_euro:.2f} EUR'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })


@staff_member_required
def get_unique_values(request):
    perfumers = Fragrance.objects.values_list('perfumer', flat=True).order_by('perfumer').distinct()
    origins = PerfumeTransaction.objects.values_list('origin', flat=True).exclude(origin__in=['Dubai/Kristina', 'Dubai Fair']).order_by('origin').distinct()
    bottles = PerfumeTransaction.objects.values_list('bottle', flat=True).order_by('bottle').distinct()
    packages = PerfumeTransaction.objects.values_list('package', flat=True).order_by('package').distinct()
    locations = ['Dubai','London','Moscow','Paris']
    currencies = PerfumeTransaction.objects.values_list('purchase_currency', flat=True).order_by('purchase_currency').distinct()

    return JsonResponse({
        'perfumers': list(perfumers),
        'origins': list(origins),
        'bottles': list(bottles),
        'packages': list(packages),
        'locations': list(locations),
        'currencies': list(currencies)
    })

@staff_member_required
def get_transactions(request):
    perfumer = request.GET.get('perfumer')
    fragrance = request.GET.get('fragrance')

    query = PerfumeTransaction.objects.all()
    if perfumer:
        query = query.filter(perfumer=perfumer)
    if fragrance:
        query = query.filter(fragrance=fragrance)

    purchases = query.all()
    sales = query.exclude(sale_date__isnull=True)

    return JsonResponse({
        'purchases': list(purchases.values()),
        'sales': list(sales.values())
    })

@staff_member_required
def all_transactions(request):
    perfumers = PerfumeTransaction.objects.values_list('perfumer', flat=True).order_by('perfumer').distinct()
    fragrances = PerfumeTransaction.objects.values_list('fragrance', flat=True).order_by('fragrance').distinct()
    transactions = PerfumeTransaction.objects.all()

    return render(request, 'transactions.html', {
        'perfumers': perfumers,
        'fragrances': fragrances,
        'transactions': transactions
    })
@staff_member_required
def get_fragrances_2(request):
    perfumer = request.GET.get('perfumer')
    fragrances = PerfumeTransaction.objects.filter(perfumer=perfumer).values_list('fragrance', flat=True).order_by('fragrance').distinct()
    return JsonResponse(list(fragrances), safe=False)


PERFUME_EDITABLE_FIELDS = {
    'fragrance', 'perfumer', 'location', 'package', 'bottle', 'origin',
    'listed_price_ruble', 'listed_price_aed',
}

@require_POST
@staff_member_required
def update_perfume(request):
    data = json.loads(request.body)
    field = data.get('field')
    if field not in PERFUME_EDITABLE_FIELDS:
        return JsonResponse({'status': 'error', 'message': 'Field not editable'}, status=400)
    perfume = get_object_or_404(PerfumeTransaction, id=data['perfume_id'])
    setattr(perfume, field, data['value'])
    perfume.save()
    return JsonResponse({'status': 'success'})


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password1']
        location = request.POST['location']

        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, location=location)
        return redirect('login')
    return render(request, 'registration/register.html')

def get_perfume_images(request, id):

    perfume = get_object_or_404(PerfumeTransaction, id=id)
    images = [{'id': img.id, 'url': img.image.url} for img in perfume.perfumepicture_set.all()]
    return JsonResponse({'images': images})

@csrf_exempt
def upload_images(request, id):
    perfume = get_object_or_404(PerfumeTransaction, id=id)
    for image in request.FILES.getlist('images'):
        PerfumePicture.objects.create(perfume=perfume, image=image)
    return JsonResponse({'status': 'success'})

@csrf_exempt
def delete_image(request, image_id):
    image = get_object_or_404(PerfumePicture, id=image_id)
    image.delete()
    return JsonResponse({'status': 'success'})

def welcome_view(request):
    return render(request, 'welcome.html')


def welcome_view_ru(request):
    return render(request, 'welcome_ru.html')

def catalog_view(request):
    user_location = request.user.userprofile.location if not request.user.is_staff else None
    perfumes = PerfumeTransaction.objects.filter(sale_date__isnull=True).order_by('perfumer', 'fragrance').prefetch_related('perfumepicture_set')
    if not request.user.is_staff:
        perfumes = perfumes.filter(location=user_location)

    context = {
        'perfumes': perfumes,
        'is_staff': request.user.is_staff,
        'user_location': user_location
    }
    return render(request, 'catalog.html', context)


def catalog_view_ru(request):
    perfumes = PerfumeTransaction.objects.filter(sale_date__isnull=True).order_by('perfumer', 'fragrance').prefetch_related('perfumepicture_set')
    perfumes = perfumes.filter(location='Moscow')

    context = {
        'perfumes': perfumes,
    }
    return render(request, 'catalog_ru.html', context)

def get_filtered_options(request):
    selected_perfumer = request.GET.get('perfumer')
    selected_fragrance = request.GET.get('fragrance')
    selected_location = request.GET.get('location')

    queryset = PerfumeTransaction.objects.filter(sale_date__isnull=True).prefetch_related('perfumepicture_set')

    if selected_perfumer:
        queryset = queryset.filter(perfumer=selected_perfumer)
    if selected_fragrance:
        queryset = queryset.filter(fragrance=selected_fragrance)
    if selected_location:
        queryset = queryset.filter(location=selected_location)

    perfumes_data = []
    for perfume in queryset:
            pictures = [pic.image.url for pic in perfume.perfumepicture_set.all()]
            perfumes_data.append({
                'id': perfume.id,
                'perfumer': perfume.perfumer,
                'fragrance': perfume.fragrance,
                'location': perfume.location,
                'bottle': perfume.bottle,
                'package': perfume.package,
                'listed_price_ruble': perfume.listed_price_ruble,
                'pictures': pictures
            })
    return JsonResponse({
        'perfumers': list(queryset.values_list('perfumer', flat=True).distinct().order_by('perfumer')),
        'fragrances': list(queryset.values_list('fragrance', flat=True).distinct().order_by('fragrance')),
        'locations': list(queryset.values_list('location', flat=True).distinct()),
         'perfumes' : perfumes_data,
    })

@staff_member_required
def index(request):
    return render(request, 'index.html')


@staff_member_required
def fragrance_list(request):
    if request.method == 'POST':
        perfumer = request.POST.get('perfumer', '').strip()
        fragrance_name = request.POST.get('fragrance', '').strip()
        if perfumer and fragrance_name:
            Fragrance.objects.create(perfumer=perfumer, fragrance=fragrance_name)
        return redirect('fragrance_list')

    perfumer_filter = request.GET.get('perfumer', '')
    fragrances = Fragrance.objects.all().order_by('perfumer', 'fragrance')
    if perfumer_filter:
        fragrances = fragrances.filter(perfumer__icontains=perfumer_filter)

    return render(request, 'fragrance_list.html', {
        'fragrances': fragrances,
        'perfumer_filter': perfumer_filter,
    })

@staff_member_required
def update_fragrance(request, pk):
    if request.method == 'POST':
        fragrance_obj = get_object_or_404(Fragrance, pk=pk)
        perfumer = request.POST.get('perfumer', '').strip()
        fragrance_name = request.POST.get('fragrance', '').strip()
        if perfumer and fragrance_name:
            fragrance_obj.perfumer = perfumer
            fragrance_obj.fragrance = fragrance_name
            fragrance_obj.save()
    return redirect('fragrance_list')

@staff_member_required
def get_fragrances(request):
    perfumer = request.GET.get('perfumer')
    fragrances = Fragrance.objects.filter(perfumer=perfumer).values_list('fragrance', flat=True)
    return JsonResponse({'fragrances': list(fragrances)})

@staff_member_required
def add_fragrance(request):
    """API view to add a new fragrance"""
    if request.method == 'POST':
        data = json.loads(request.body)
        fragrance = Fragrance(
            perfumer=data.get('perfumer'),
            fragrance=data.get('fragrance')
        )
        fragrance.save()
        return JsonResponse({'success': True, 'id': fragrance.id})
    return JsonResponse({'success': False}, status=400)
@staff_member_required
def PerfumeAppView(request):
    perfumes = PerfumeTransaction.objects.all().values()
    template = loader.get_template('all_perfumes.html')
    context = {
    'perfumes': perfumes,
      }
    return HttpResponse(template.render(context, request))


def all_time_financial_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 1. INITIAL QUERYSET AND DATE FILTERING
    # This ensures only transactions within the exact date range are selected.
    queryset = PerfumeTransaction.objects.all()

    if start_date and end_date:
        # Transactions must have EITHER the purchase date OR the sale date
        # strictly within the user-defined date range (YYYY-MM-DD).
        combined_filter = (
                Q(purchase_date__gte=start_date, purchase_date__lte=end_date) |
                Q(sale_date__gte=start_date, sale_date__lte=end_date)
        )
        queryset = queryset.filter(combined_filter)

    elif start_date:
        # Handle case where only start_date is provided
        combined_filter = (
                Q(purchase_date__gte=start_date) |
                Q(sale_date__gte=start_date)
        )
        queryset = queryset.filter(combined_filter)

    elif end_date:
        # Handle case where only end_date is provided
        combined_filter = (
                Q(purchase_date__lte=end_date) |
                Q(sale_date__lte=end_date)
        )
        queryset = queryset.filter(combined_filter)

    # 2. CREATE DATAFRAME AND GENERATE MONTHLY REPORT

    data = list(queryset.values())
    df_transactions = pd.DataFrame.from_records(data)

    if df_transactions.empty:
        context = {
            'columns': [],
            'data': [],
            'sums': {},
            'start_date': start_date,
            'end_date': end_date
        }
        return render(request, 'financial_report.html', context)

    # df_report aggregates the filtered transactions and groups them by month.
    df_report = Transactions.all_time_report(df_transactions)

    # 3. FINAL VISUAL FILTER (Ensures only relevant MONTH ROWS are shown)
    # This prevents grouping anomalies (e.g., seeing all of December if the range ends Jan 1).
    if start_date and end_date:
        # Convert user's full dates to YYYY-MM strings for month-level row comparison.
        start_month_str = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m')
        end_month_str = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m')

        # Filter rows where the 'month' column is within the calendar month range.
        df_report = df_report[
            (df_report['month'].astype(str) >= start_month_str) &
            (df_report['month'].astype(str) <= end_month_str)
            ]

    # Handle case where the report is empty after final month filter
    if df_report.empty:
        context = {
            'columns': df_report.columns.tolist(),
            'data': [],
            'sums': {},
            'start_date': start_date,
            'end_date': end_date
        }
        return render(request, 'financial_report.html', context)

    # 4. RECALCULATE SUMS AND RENDER
    sums = {
        col: df_report[col].sum()
        for col in df_report.columns
        if (pd.api.types.is_numeric_dtype(df_report[col]) and col != 'Premium %')
    }

    context = {
        'columns': df_report.columns.tolist(),
        'data': df_report.to_dict('records'),
        'sums': sums,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'financial_report.html', context)


def inventory_list(request):
    transactions = PerfumeTransaction.objects.filter(sale_date__isnull=True).order_by('location','perfumer', 'fragrance', 'purchase_date')
    perfumers = PerfumeTransaction.objects.values_list('perfumer', flat=True).distinct().order_by('perfumer')
    fragrance_names = PerfumeTransaction.objects.values_list('fragrance', flat=True).distinct().order_by('fragrance')
    locations = PerfumeTransaction.objects.values_list('location', flat=True).distinct()

    return render(request, 'inventory_list.html', {
        'transactions': transactions,
        'perfumers': perfumers,
        'fragrance_names': fragrance_names,
        'locations': locations,
    })

@require_POST
@staff_member_required
def update_perfume_edit(request, id):
    try:
        data = json.loads(request.body)
        transaction = get_object_or_404(PerfumeTransaction, id=id)
        transaction.fragrance = data['fragrance']
        transaction.location = data['location']
        transaction.package = data['package']
        transaction.bottle = data['bottle']
        transaction.listed_price_ruble = data['listed_price_ruble']
        transaction.listed_price_aed = data['listed_price_aed']
        transaction.save()
        return JsonResponse({'status': 'success'})
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Update failed'}, status=400)

@require_POST
@staff_member_required
def delete_transaction(request, id):
    transaction = get_object_or_404(PerfumeTransaction, id=id)
    transaction.delete()
    return JsonResponse({'status': 'success'})

@require_POST
@staff_member_required
def reset_sale(request, id):
    transaction = get_object_or_404(PerfumeTransaction, id=id)
    transaction.sale_date = None
    transaction.sale_price = None
    transaction.sale_currency = None
    transaction.sale_exch_rate = None
    transaction.sale_price_eur = None
    transaction.earnings_eur = None
    transaction.premium = None
    transaction.save()
    return JsonResponse({'status': 'success'})

@staff_member_required
def get_perfume_data(request, id):
    try:
        transaction = get_object_or_404(PerfumeTransaction, id=id)
        exchange = Tools.CurrencyExchange("EUR")
        exch_rate_rub = exchange.get_rate('RUB')
        exch_rate_aed = exchange.get_rate('AED')
        target_premium=GlobalParameters.TARGET_PREMIUM
        target_price_rub=round(transaction.purchase_price_euro*exch_rate_rub*(1.+target_premium),-3)
        target_price_aed=round(transaction.purchase_price_euro*exch_rate_aed*(1.+target_premium),-1)


        data = {
            'perfumer': transaction.perfumer,
            'fragrance': transaction.fragrance,
            'purchase_date': transaction.purchase_date.strftime('%Y-%m-%d'),
            'price': str(transaction.price),
            'purchase_currency': str(transaction.purchase_currency),
            'origin': transaction.origin,
            'location': transaction.location,
            'package': transaction.package,
            'bottle': transaction.bottle,
            'listed_price_ruble': target_price_rub,
            'listed_price_aed': target_price_aed,
        }


        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def sell_perfume(request, id):
    if request.method == 'POST':
        exchange = Tools.CurrencyExchange("EUR")


        try:
            data = json.loads(request.body)
             # Get current EUR to sale currency rate
            exch_rate = exchange.get_rate(data['sale_currency'])
            if exch_rate is None:
                exch_rate=GlobalParameters.EXCHANGE_RATES[data['sale_currency']]
            transaction = get_object_or_404(PerfumeTransaction, id=id)
            transaction.sale_date = datetime.strptime(data['sale_date'], '%Y-%m-%d')
            transaction.sale_price = float(data['sale_price'])
            transaction.sale_currency = data['sale_currency']
            transaction.sale_exch_rate = exch_rate
            transaction.sale_price_eur = float(data['sale_price']) / exch_rate
            transaction.earnings_eur=transaction.sale_price_eur-transaction.purchase_price_euro
            transaction.premium=transaction.earnings_eur/transaction.purchase_price_euro
            transaction.location='Sold'
            transaction.discount=0.
            transaction.vat_back=0.
            transaction.sale_year=transaction.sale_date.year
            transaction.sale_month=transaction.sale_date.month
            transaction.save()

            return_data = {
            'perfumer': transaction.perfumer,
            'fragrance': transaction.fragrance,
            'package': transaction.package,
            'bottle': transaction.bottle,
            'sale_price': transaction.sale_price,
            'exch_rate': transaction.sale_exch_rate,
            'sale_price_eur': transaction.sale_price_eur,
            'earnings_eur': transaction.earnings_eur,
            'premium': transaction.premium,
            'sale_date': transaction.sale_date,
            'sale_currency': data['sale_currency'],
        }

            return JsonResponse({'status': 'success','body':return_data})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

def purchase_list(request):
    perfumer_filter = request.GET.get('perfumer', '')
    fragrance_filter = request.GET.get('fragrance', '')
    location_filter = request.GET.get('location', '')

    purchases = PerfumeTransaction.objects.exclude(location='Sold')
    if perfumer_filter:
        purchases = purchases.filter(perfumer=perfumer_filter)
    if fragrance_filter:
        purchases = purchases.filter(fragrance=fragrance_filter)
    if location_filter:
        purchases = purchases.filter(location=location_filter)
    purchases = purchases.order_by('purchase_date', 'perfumer', 'fragrance')

    base_qs = PerfumeTransaction.objects.exclude(location='Sold')
    all_perfumers = list(base_qs.values_list('perfumer', flat=True).distinct().order_by('perfumer'))
    all_fragrances = list(base_qs.values_list('fragrance', flat=True).distinct().order_by('fragrance'))
    all_locations = list(base_qs.values_list('location', flat=True).distinct().order_by('location'))

    context = {
        'purchases': purchases,
        'all_perfumers': all_perfumers,
        'all_fragrances': all_fragrances,
        'all_locations': all_locations,
        'perfumer_filter': perfumer_filter,
        'fragrance_filter': fragrance_filter,
        'location_filter': location_filter,
    }

    return render(request, 'purchase_list.html', context)
