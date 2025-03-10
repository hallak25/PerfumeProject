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
from django.db import connection
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User


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
                listed_price_aed=round(price_euro*(1.+GlobalParameters.TARGET_PREMIUM)*GlobalParameters.EXCHANGE_RATES['AED']-1)

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
    locations = PerfumeTransaction.objects.values_list('location', flat=True).exclude(location__in=['Sold']).order_by('location').distinct()
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


@require_POST
@staff_member_required
def update_perfume(request):
    data = json.loads(request.body)
    perfume = PerfumeTransaction.objects.get(id=data['perfume_id'])
    setattr(perfume, data['field'], data['value'])
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
@login_required
def welcome_view(request):
    return render(request, 'welcome.html')
@login_required
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
def add_perfume_transaction(request):
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                purchase_price=float(request.POST.get('price'))
                purchase_exch_rate=GlobalParameters.EXCHANGE_RATES[request.POST.get('currency')]
                sql_command=f'INSERT INTO "PerfumeApp_perfumetransaction" ("Perfumer", "Fragrance", "Package", "Bottle", "Origin", "Location", "Price", "Purchase Currency","Purchase date","Discount","VAT back","Purch Exch Rate","Purchase Price (euro)")'
                sql_command+=f"  VALUES ('{request.POST.get('perfumer')}', '{request.POST.get('fragrance')}', '{request.POST.get('package')}', '{request.POST.get('bottle')}', '{request.POST.get('origin')}',"
                sql_command+=f" '{request.POST.get('location')}',{purchase_price},'{request.POST.get('currency')}','{request.POST.get('date', date.today())}',{0.},{0.},{purchase_exch_rate},{purchase_price/purchase_exch_rate})"

                cursor.execute(sql_command)

            messages.add_message(request,messages.INFO, 'purchase added!')
            return JsonResponse({
                'status': 'success',
                'message': 'Transaction added successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to add transaction. Please check your inputs.'
            }, status=400)

    context = {
        'perfumers': Fragrance.objects.values_list('perfumer', flat=True).distinct().order_by('perfumer'),
        'fragrances': Fragrance.objects.values_list('fragrance', flat=True).distinct().order_by('fragrance'),
        'packages': PerfumeTransaction.objects.values_list('package', flat=True).distinct().order_by(),
        'bottles': PerfumeTransaction.objects.values_list('bottle', flat=True).distinct().order_by(),
        'origins': PerfumeTransaction.objects.values_list('origin', flat=True).distinct().order_by(),
        'locations': GlobalParameters.ALL_LOCATIONS,
        'currencies': PerfumeTransaction.objects.values_list('purchase_currency', flat=True).distinct().order_by(),
        'today': date.today()
    }
    return render(request, 'add_perfume_transaction.html', context)

@staff_member_required
def fragrance_list(request):
    """View to render the fragrance list page"""
    return render(request, 'fragrance_list.html')

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

def StockView(request,location='All'):
    perfumes = PerfumeTransaction.objects.all().values()
    df = pd.DataFrame.from_records(perfumes)
    df_inventory= df[df['sale_date'].isnull()]
    if location!='All':
        df_inventory= df_inventory[df_inventory['location']==location]
    df_inventory = df_inventory[['perfumer','fragrance','origin','location','package','bottle', 'price','purchase_currency', 'purchase_price_euro', 'purchase_date']].copy()
    df_inventory=df_inventory.sort_values(['purchase_date','perfumer','fragrance'])
    html = df_inventory.to_html()
    return HttpResponse(html)

def StockViewParis(request):
    return StockView(request,location='Paris') 

def StockViewLondon(request):
    return StockView(request,location='London')

def StockViewDubai(request):
    return StockView(request,location='Dubai') 

def StockViewMoscow(request):
    return StockView(request,location='Moscow') 

def main(request):
  template = loader.get_template('main.html')
  return HttpResponse(template.render())


def all_time_financial_report(request):
    # Create transaction DataFrame from database
    df_transactions = pd.DataFrame.from_records(PerfumeTransaction.objects.all().values())
    df_report=Transactions.all_time_report(df_transactions)


    # Calculate column sums (for numeric columns)
    sums = {
        col: df_report[col].sum()
        for col in df_report.columns
        if (pd.api.types.is_numeric_dtype(df_report[col]) and col!='Premium %')
    }

    # Convert DataFrame to dictionary for template
    context = {
        'columns': df_report.columns.tolist(),
        'data': df_report.to_dict('records'),
        'sums': sums
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

@csrf_exempt
def update_perfume_edit(request, id):
    if request.method == 'POST':
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
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

def get_perfume_data(request, id):
    try:
        transaction = get_object_or_404(PerfumeTransaction, id=id)

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
            'listed_price_ruble': transaction.listed_price_ruble,
            'listed_price_aed': transaction.listed_price_aed,
        }


        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def sell_perfume(request, id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            transaction = get_object_or_404(PerfumeTransaction, id=id)
            transaction.sale_date = datetime.strptime(data['sale_date'], '%Y-%m-%d')
            transaction.sale_price = float(data['sale_price'])
            transaction.sale_exch_rate = GlobalParameters.EXCHANGE_RATES[data['sale_currency']]
            transaction.sale_price_eur = float(data['sale_price']) / GlobalParameters.EXCHANGE_RATES[data['sale_currency']]
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
            'sale_price_eur': transaction.sale_price_eur,
            'earnings_eur': transaction.earnings_eur,
            'premium': transaction.premium,
            'sale_date': transaction.sale_date,
        }

            return JsonResponse({'status': 'success','body':return_data})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

def purchase_list(request):
    # Get all transactions
    df_purchases = pd.DataFrame.from_records(PerfumeTransaction.objects.all().values())

    # Get filter parameters from request
    perfumer_filter = request.GET.get('perfumer', '')
    fragrance_filter = request.GET.get('fragrance', '')
    location_filter = request.GET.get('location', '')

    # Apply filters if they exist
    df_purchases = df_purchases[df_purchases['location']!='Sold']
    if perfumer_filter:
        df_purchases = df_purchases[df_purchases['perfumer']==perfumer_filter]
    if fragrance_filter:
        df_purchases = df_purchases[df_purchases['fragrance']==fragrance_filter]
    if location_filter:
        df_purchases = df_purchases[df_purchases['location']==location_filter]

    # Get unique values for dropdowns
    #all_perfumers = PerfumeTransaction.objects.values_list('perfumer', flat=True).distinct()
    all_perfumers = list(df_purchases['perfumer'].unique())
    all_fragrances = list(df_purchases['fragrance'].unique())
    all_locations = list(df_purchases['location'].unique())
    all_perfumers.sort()
    all_fragrances.sort()
    all_locations.sort()

    context = {
        'purchases': df_purchases.to_dict('records'),
        'all_perfumers': all_perfumers,
        'all_fragrances': all_fragrances,
        'all_locations': all_locations,
        'perfumer_filter': perfumer_filter,
        'fragrance_filter': fragrance_filter,
        'location_filter': location_filter,
    }

    return render(request, 'purchase_list.html', context)
