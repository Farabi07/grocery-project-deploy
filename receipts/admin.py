from django.contrib import admin
from .models import *

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
	list_display = [field.name for field in ExpenseCategory._meta.fields]
	
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Transaction._meta.fields]
	
@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Receipt._meta.fields]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Payment._meta.fields]
	list_filter = ('subscription',)
	search_fields = ('transaction_id', 'subscription__user__username')
	ordering = ('-created_at',)