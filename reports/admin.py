from django.contrib import admin
from .models import *

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Report._meta.fields]