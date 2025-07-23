from enum import unique
from operator import truediv
from statistics import mode
from django.db import models
from django.db.models.fields import BigAutoField
from django.utils import tree
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth import get_user_model
from PIL import Image
from rest_framework.serializers import BaseSerializer
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.hashers import make_password, check_password, identify_hasher



class Permission(models.Model):
    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.replace(' ', '_').upper()
        super().save(*args, **kwargs)


class Role(models.Model):
    name = models.CharField(max_length=255)
    # permissions = models.ManyToManyField(Permission, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    
    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.replace(' ', '_').upper()
        super().save(*args, **kwargs)




class Designation(models.Model):
    name = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super().save(*args, **kwargs)




class Country(models.Model):
    name = models.CharField(max_length=255)
    capital_name = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=255, null=True, blank=True)
    country_code2 = models.CharField(max_length=255, null=True, blank=True)
    phone_code = models.CharField(max_length=255, null=True, blank=True)
    currency_code = models.CharField(max_length=255, null=True, blank=True)
    continent_name = models.CharField(max_length=255, null=True, blank=True)
    continent_code = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name




class City(models.Model):
    name = models.CharField(max_length=50)
    bn_name = models.CharField(max_length=50, null=True, blank=True)

    lat = models.CharField(max_length=255, null=True, blank=True)
    lon = models.CharField(max_length=255, null=True, blank=True)

    url = models.CharField(max_length=500, null=True, blank=True)

    country = models.ForeignKey(Country, on_delete= models.RESTRICT, related_name='cities')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        ordering = ('id',)
        verbose_name_plural = 'Cities'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        super().save(*args, **kwargs)


class Branch(models.Model):
    name = models.CharField(max_length=50)
    
    short_desc = models.TextField(blank=True, null=True)
    full_desc = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    street_address_one = models.CharField(max_length=255, null=True, blank=True)
    street_address_two = models.CharField(max_length=255, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    postal_code = models.CharField(max_length=50, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Branches'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        super().save(*args, **kwargs)




class UserManager(BaseUserManager):
    def create_user(self, first_name=None, last_name=None,full_name=None, email=None, gender='male', password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            full_name=None,
            email=self.normalize_email(email),
            gender=gender,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, gender, password=None, **extra_fields):
        user = self.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            **extra_fields
        )
        user.is_admin = True
        user.is_superuser = True
        # user.is_staff = True
        user.save(using=self._db)
        return user
 



class User(AbstractBaseUser):
    class Gender(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')
        OTHERS = 'others', _('Others')
        
    full_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True, unique=True)
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)

    gender = models.CharField(max_length=6, choices=Gender.choices, default=Gender.MALE,null=True, blank=True)

    primary_phone = PhoneNumberField(null=True, blank=True, unique=True)
    secondary_phone = PhoneNumberField(null=True, blank=True, unique=True)

    user_type = models.CharField(max_length=255, null=True, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True,default='admin')

    street_address_one = models.CharField(max_length=255, null=True, blank=True)
    street_address_two = models.CharField(max_length=255, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    postal_code = models.CharField(max_length=50, null=True, blank=True)

    image = models.ImageField(upload_to="users/", default='users/default_profile_pic.png', null=True, blank=True)
    nid = models.CharField(max_length=32, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'gender']

    class Meta:
        ordering = ('first_name',)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.role:
            self.role = 'admin' 
        super().save(*args, **kwargs)
        
        if self.image:
            max_width, max_height = 750, 1000
            path = self.image.path
            image = Image.open(path)
            width, height = image.size
            if width > max_width or height > max_height:
                if width > height:
                    w_h = (1000, 750)
                elif height > width:
                    w_h = (750, 1000)
                img = image.resize(w_h)
                img.save(path)  
        else:
            self.image = None
            super().save(update_fields=['image'])

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        
        # Simplest possible answer: Yes, always
        return True
    
    def get_all_permissions(self, obj=None):
        # This method should return a set of all permissions for the user.
        # You can obtain the permissions using the `Permission` model.
        if not self.is_active:
            return set()

        if not hasattr(self, '_user_perm_cache'):
            user_permissions = Permission.objects.filter(user=self)
            user_permissions = user_permissions.values_list('content_type__app_label', 'codename').order_by()
            self._user_perm_cache = {
                "%s.%s" % (ct, name) for ct, name in user_permissions
            }
        return self._user_perm_cache

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Employee(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True, related_name='employee_user')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='employees')
    name = models.CharField(max_length=255, null=True, blank=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    # phone = PhoneNumberField(null=True, blank=True, unique=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    # role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    password = models.CharField(max_length=255,null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True, default='employee')
    image = models.ImageField(upload_to="employee/", default='employee/default_profile_pic.png', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="+", null=True, blank=True)
    
    class Meta:
        ordering = ('id',)
        verbose_name_plural = 'Employees'

    @property
    def full_name(self):
        return self.name or ""

    def __str__(self):
        return self.full_name or self.email or ""

    def save(self, *args, **kwargs):
        # Hash password only if not hashed
        if self.password:
            try:
                identify_hasher(self.password)  # Checks if password is hashed
            except ValueError:
                # Not hashed yet, so hash it now
                self.password = make_password(self.password)
        super().save(*args, **kwargs)
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

class LoginHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)

    ip_address = models.CharField(max_length=255, null=True, blank=True)
    mac_address = models.CharField(max_length=255, null=True, blank=True)
    g_location_info = models.CharField(max_length=500, null=True, blank=True)
    is_device_blocked = models.BooleanField(default=False)

    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        verbose_name_plural = 'LoginHistories'
        ordering = ('-id',)

    def __str__(self):
        return self.user.username if self.user else self.user
    
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    plan_id = models.CharField(max_length=100, unique=True)  # PayPal/Stripe plan id
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    
    
class Subscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)  # Subscription start date
    expires_at = models.DateTimeField(null=True, blank=True)  # Subscription expiry date
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    trial_started_at = models.DateTimeField(null=True, blank=True)  # Trial start datetime
    trial_used = models.BooleanField(default=False)  # Has trial been used/ended?
    payment_method_token = models.CharField(max_length=255,blank=True, null=True)  # Token for payment method (e.g., Stripe token)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True
    )

    def is_trial_active(self):
        if self.trial_started_at and not self.trial_used:
            trial_end = self.trial_started_at + timezone.timedelta(days=7)
            if timezone.now() <= trial_end:
                return True  # ✅ trial is still active
            else:
                self.trial_used = True
                self.save(update_fields=['trial_used'])  # ✅ mark it used
        return False  # trial expired or already used


    def is_subscription_active(self):
        """Check if subscription is currently active."""
        if self.is_active and self.expires_at and self.expires_at > timezone.now():
            return True
        return False

    def can_use_app(self):
        """User can use app if trial OR subscription is active."""
        return self.is_trial_active() or self.is_subscription_active()

    def __str__(self):
        status = "Active" if self.can_use_app() else "Inactive"
        return f"{self.user.email} Subscription - {status}"


class ScanUsage(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scan_count = models.PositiveIntegerField(default=0)
    last_scan_date = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    class Meta:
        verbose_name_plural = 'Scan Usages'
    def __str__(self):
        return f"{self.user.email} Scan Usage - {self.scan_count} scans"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    reset_token = models.UUIDField(null=True, blank=True, unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    def is_expired(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).seconds > 300  # 5 minutes