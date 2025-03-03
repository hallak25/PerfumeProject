from django.urls import path,include
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    path('index/', views.index, name='index'),
    path('main/', views.main, name='main'),
    path('PerfumeAppView/', views.PerfumeAppView, name='PerfumeAppView'),
    path('StockViewParis/', views.StockViewParis, name='StockViewParis'),
    path('StockViewLondon/', views.StockViewLondon, name='StockViewLondon'),
    path('StockViewDubai/', views.StockViewDubai, name='StockViewDubai'),
    path('StockViewMoscow/', views.StockViewMoscow, name='StockViewMoscow'),
    path('fragrances/list/', views.fragrance_list, name='fragrance_list'),
    path('fragrances/', views.get_fragrances, name='get_fragrances'),
    path('fragrances/add/', views.add_fragrance, name='add_fragrance'),
    path('financial_report/', views.all_time_financial_report, name='financial_report'),
    path('purchase_list/', views.purchase_list, name='purchase_list'),
    path('add_transaction/', views.add_perfume_transaction, name='add_transaction'),
    path('inventory_list/', views.inventory_list, name='inventory_list'),
    path('sell/<int:id>/', views.sell_perfume, name='sell_perfume'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('get-filtered-options/', views.get_filtered_options, name='get_filtered_options'),
    path('get-pictures/<int:perfume_id>/', views.get_pictures, name='get_pictures'),
    path('upload-pictures/', views.upload_pictures, name='upload_pictures'),
    path('register/', views.register, name='register'),
    path('update-perfume/', views.update_perfume, name='update_perfume'),
]

urlpatterns += staticfiles_urlpatterns()

