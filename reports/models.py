from django.db import models
from django.conf import settings
from django.db import models
from authentication.models import User
from receipts.models import ExpenseCategory

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()  
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    

    def __str__(self):
        return f"Report for {self.user.username} - {self.month}"

