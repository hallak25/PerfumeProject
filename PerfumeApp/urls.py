from django.urls import path,include
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('index/', views.index, name='index'),
    path('main/', views.main, name='main'),
    path('', views.welcome_view, name='welcome'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
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
    path('update/<int:id>/', views.update_perfume_edit, name='update_perfume_edit'),
    path('get-perfume/<int:id>/', views.get_perfume_data, name='get_perfume_data'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('get-filtered-options/', views.get_filtered_options, name='get_filtered_options'),
    path('get-perfume-images/<int:id>/', views.get_perfume_images, name='get_perfume_images'),
    path('upload-images/<int:id>/', views.upload_images, name='upload_images'),
    path('delete-image/<int:image_id>/', views.delete_image, name='delete_image'),
    path('register/', views.register, name='register'),
    path('update-perfume/', views.update_perfume, name='update_perfume'),
    path('all-transactions/', views.all_transactions, name='all_transactions'),
    path('transactions/', views.get_transactions, name='get_transactions'),
    path('get-fragrances/', views.get_fragrances_2, name='get_fragrances_2'),
]

urlpatterns += staticfiles_urlpatterns()

