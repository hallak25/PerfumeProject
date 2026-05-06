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
from django.core.cache import cache


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

def _get_live_rates():
    rates = cache.get('live_exchange_rates')
    if rates is None:
        exchanger = Tools.CurrencyExchange("EUR")
        exchanger.fetch_rates()
        eur_rub = exchanger.get_rate("RUB")
        eur_gbp = exchanger.get_rate("GBP")
        rates = {
            'eur_rub': round(eur_rub, 2) if eur_rub else None,
            'gbp_eur': round(1 / eur_gbp, 4) if eur_gbp else None,
        }
        cache.set('live_exchange_rates', rates, 600)
    return rates

@staff_member_required
def index(request):
    return render(request, 'index.html', {'rates': _get_live_rates()})


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
    selected_year = request.GET.get('year', 'all')

    # Available years across purchase_date and sale_date
    purchase_years = {d.year for d in PerfumeTransaction.objects.dates('purchase_date', 'year')}
    sale_years = {d.year for d in PerfumeTransaction.objects.dates('sale_date', 'year')}
    available_years = sorted(purchase_years | sale_years, reverse=True)

    queryset = PerfumeTransaction.objects.all()
    if selected_year != 'all':
        try:
            year_int = int(selected_year)
            queryset = queryset.filter(
                Q(purchase_date__year=year_int) | Q(sale_date__year=year_int)
            )
        except ValueError:
            selected_year = 'all'

    df_transactions = pd.DataFrame.from_records(list(queryset.values()))

    base_context = {
        'available_years': available_years,
        'selected_year': selected_year,
    }

    if df_transactions.empty:
        return render(request, 'financial_report.html', {
            **base_context,
            'columns': [],
            'data': [],
            'sums': {},
        })

    df_report = Transactions.all_time_report(df_transactions)

    if selected_year != 'all':
        df_report = df_report[df_report['month'].astype(str).str.startswith(str(selected_year))]

    if df_report.empty:
        return render(request, 'financial_report.html', {
            **base_context,
            'columns': df_report.columns.tolist(),
            'data': [],
            'sums': {},
        })

    sums = {
        col: df_report[col].sum()
        for col in df_report.columns
        if (pd.api.types.is_numeric_dtype(df_report[col]) and col != 'Premium %')
    }
    total_sales = sums.get('Total Sales (EUR)', 0)
    total_earnings = sums.get('Earnings (EUR)', 0)
    cost = total_sales - total_earnings
    if cost:
        sums['Premium %'] = int(round(total_earnings / cost * 100))

    return render(request, 'financial_report.html', {
        **base_context,
        'columns': df_report.columns.tolist(),
        'data': df_report.to_dict('records'),
        'sums': sums,
    })


@staff_member_required
def sales_review(request):
    sold_qs = PerfumeTransaction.objects.exclude(sale_date__isnull=True)

    available_years = sorted(
        {d.year for d in sold_qs.dates('sale_date', 'year')},
        reverse=True,
    )

    if not available_years:
        return render(request, 'sales_review.html', {
            'available_years': [],
            'no_data': True,
        })

    selected_year = int(request.GET.get('year', available_years[0]))

    year_qs = sold_qs.filter(sale_date__year=selected_year)

    if not year_qs.exists():
        return render(request, 'sales_review.html', {
            'available_years': available_years,
            'selected_year': selected_year,
            'no_data': True,
        })

    df = pd.DataFrame.from_records(year_qs.values(
        'perfumer', 'fragrance', 'purchase_price_euro',
        'sale_price_eur', 'earnings_eur',
    ))
    df = df.fillna(0)
    # Recompute margin per-row from earnings/cost so it stays consistent with
    # the aggregate weighted formula (avoids drift from stale stored premiums).
    df['margin_pct'] = df.apply(
        lambda r: (r['earnings_eur'] / r['purchase_price_euro'] * 100)
                  if r['purchase_price_euro'] else 0,
        axis=1,
    )

    total_revenue = float(df['sale_price_eur'].sum())
    total_profit = float(df['earnings_eur'].sum())
    units_sold = int(len(df))
    total_cost = total_revenue - total_profit
    avg_margin = (total_profit / total_cost * 100) if total_cost else 0.0

    # Brand analysis
    brand_stats = df.groupby('perfumer').agg(
        revenue=('sale_price_eur', 'sum'),
        profit=('earnings_eur', 'sum'),
        units=('perfumer', 'count'),
    ).reset_index()
    brand_cost = brand_stats['revenue'] - brand_stats['profit']
    brand_stats['avg_margin'] = (brand_stats['profit'] / brand_cost.where(brand_cost != 0) * 100).fillna(0)
    if total_profit:
        brand_stats['profit_share'] = (brand_stats['profit'] / total_profit * 100).round(1)
    else:
        brand_stats['profit_share'] = 0.0

    top_by_profit = brand_stats.sort_values('profit', ascending=False).head(5)
    recommended_brand = top_by_profit.iloc[0].to_dict()

    # Fragrance breakdown for each of the top 5 perfumers, ranked by profit
    fragrances_by_perfumer = {}
    for perfumer_name in top_by_profit['perfumer']:
        perf_df = df[df['perfumer'] == perfumer_name]
        frag_stats = perf_df.groupby('fragrance').agg(
            revenue=('sale_price_eur', 'sum'),
            profit=('earnings_eur', 'sum'),
            units=('fragrance', 'count'),
        ).reset_index()
        frag_cost = frag_stats['revenue'] - frag_stats['profit']
        frag_stats['avg_margin'] = (
            frag_stats['profit'] / frag_cost.where(frag_cost != 0) * 100
        ).fillna(0)
        frag_stats = frag_stats.sort_values('profit', ascending=False).head(10)
        fragrances_by_perfumer[perfumer_name] = [
            {
                'fragrance': str(r['fragrance']),
                'profit': float(r['profit']),
                'units': int(r['units']),
                'avg_margin': float(r['avg_margin']),
            }
            for _, r in frag_stats.iterrows()
        ]

    # Margin segmentation: <25%, 5%-wide bands from 25% to 150%, >150%
    inner_edges = list(range(25, 155, 5))  # 25, 30, ..., 150
    bins = [-1e9] + inner_edges + [1e9]
    labels = (
        ['<25%']
        + [f'{inner_edges[i]}-{inner_edges[i+1]}%' for i in range(len(inner_edges) - 1)]
        + ['>150%']
    )
    df['margin_segment'] = pd.cut(df['margin_pct'], bins=bins, labels=labels)

    margin_stats = df.groupby('margin_segment', observed=False).agg(
        units=('margin_segment', 'count'),
        revenue=('sale_price_eur', 'sum'),
        profit=('earnings_eur', 'sum'),
    ).reset_index()
    margin_stats['margin_segment'] = margin_stats['margin_segment'].astype(str)

    optimal_idx = int(margin_stats['profit'].idxmax())
    optimal_segment_name = margin_stats.loc[optimal_idx, 'margin_segment']
    optimal_segment_profit = float(margin_stats.loc[optimal_idx, 'profit'])
    optimal_segment_units = int(margin_stats.loc[optimal_idx, 'units'])

    margin_records = [
        {
            'segment': r['margin_segment'],
            'units': int(r['units']),
            'revenue': float(r['revenue']),
            'profit': float(r['profit']),
        }
        for _, r in margin_stats.iterrows()
    ]

    context = {
        'available_years': available_years,
        'selected_year': selected_year,
        'no_data': False,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'avg_margin': avg_margin,
        'units_sold': units_sold,
        'top_by_profit': top_by_profit.to_dict('records'),
        'fragrances_by_perfumer': fragrances_by_perfumer,
        'recommended_brand': recommended_brand,
        'margin_records': margin_records,
        'optimal_segment': optimal_segment_name,
        'optimal_segment_profit': optimal_segment_profit,
        'optimal_segment_units': optimal_segment_units,
        'chart_segments': margin_stats['margin_segment'].tolist(),
        'chart_profits': [float(x) for x in margin_stats['profit']],
    }
    return render(request, 'sales_review.html', context)


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
