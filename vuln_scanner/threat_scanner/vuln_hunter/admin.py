from django.contrib import admin
from .models import ScanJob, User, ScanResult

# Register your models here.
admin.site.register(ScanJob)
admin.site.register(ScanResult)
admin.site.register(User)
