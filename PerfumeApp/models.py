from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=30)


class ModelTest(models.Model):
  firstname = models.CharField(max_length=255)
  lastname = models.CharField(max_length=255)

class Fragrance(models.Model):
    perfumer = models.CharField(max_length=50,db_column='Perfumer', blank=True, null=True)
    fragrance = models.CharField(max_length=50,db_column='Fragrance', blank=True, null=True)


    def __str__(self):
        return f'{self.perfumer} - {self.fragrance}'


class PerfumeTransaction(models.Model):
    perfumer = models.CharField(max_length=50,db_column='Perfumer', blank=True, null=True)  
    fragrance = models.CharField(max_length=50,db_column='Fragrance', blank=True, null=True)  
    package = models.CharField(max_length=50,db_column='Package', blank=True, null=True)  
    bottle = models.CharField(max_length=50,db_column='Bottle', blank=True, null=True)  
    origin = models.CharField(max_length=50,db_column='Origin', blank=True, null=True)  
    price = models.FloatField(db_column='Price', blank=True, null=True)  
    discount = models.FloatField(max_length=50,db_column='Discount', blank=True, null=True)  
    vat_back = models.FloatField(max_length=50,db_column='VAT back', blank=True, null=True)  
    purchase_currency = models.CharField(max_length=10,db_column='Purchase Currency', blank=True, null=True)  
    purch_exch_rate = models.FloatField(db_column='Purch Exch Rate', blank=True, null=True)  
    purchase_price_euro = models.FloatField(db_column='Purchase Price (euro)', blank=True, null=True) 
    purchase_date = models.DateField(max_length=50,db_column='Purchase date', blank=True, null=True)  
    location = models.CharField(max_length=30,db_column='Location', blank=True, null=True)
    sale_currency = models.CharField(max_length=10,db_column='Sale Currency', blank=True, null=True)
    sale_exch_rate = models.FloatField(db_column='Sale Exch Rate', blank=True, null=True)  
    sale_date = models.DateField(db_column='Sale date', blank=True, null=True)  
    sale_price = models.FloatField(db_column='Sale price', blank=True, null=True)  
    sale_price_eur = models.FloatField(db_column='Sale price (EUR)', blank=True, null=True) 
    earnings_eur = models.FloatField(db_column='Earnings (EUR)', blank=True, null=True) 
    premium = models.FloatField(db_column='Premium_pct', blank=True, null=True)
    purchase_year = models.IntegerField(db_column='purchase year', blank=True, null=True)  
    purchase_month = models.IntegerField(db_column='purchase month', blank=True, null=True)  
    purchase_year_month = models.CharField(max_length=20,db_column='purchase year_month', blank=True, null=True)  
    sale_year = models.IntegerField(db_column='sale year', blank=True, null=True)  
    sale_month = models.IntegerField(db_column='sale month', blank=True, null=True)  
    sale_year_month = models.CharField(max_length=20,db_column='sale year_month', blank=True, null=True)
    listed_price_ruble = models.FloatField(db_column='listed_price_ruble', blank=True, null=True,default=0)
    listed_price_aed = models.FloatField(db_column='listed_price_aed', blank=True, null=True,default=0)

    def __str__(self):
        return f'{self.perfumer} - {self.fragrance} - {self.purchase_date}'

    def get_pictures(self):
        return self.perfumepicture_set.all()

class PerfumePicture(models.Model):
    perfume = models.ForeignKey(PerfumeTransaction, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='perfumes/')


