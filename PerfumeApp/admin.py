from django.contrib import admin

from .models import ModelTest,PerfumeTransaction,Fragrance


admin.site.register(ModelTest)
admin.site.register(PerfumeTransaction)
admin.site.register(Fragrance)
