from django.contrib import admin
from .models import Currency,Product,Order,Address

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


# Register your models here.
admin.site.register(Currency),
admin.site.register(Product),
admin.site.register(Order),
admin.site.register(Address),

from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_amount', 'min_purchase_amount', 'start_date', 'end_date', 'is_active')
    search_fields = ('code',)



class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'UserProfile'
    fk_name = 'user'

class UserAdmin(admin.ModelAdmin):
    inlines = (UserProfileInline,)
    
    # Add a custom method to display phone_number
    def phone_number(self, obj):
        return obj.userprofile.phone_number if hasattr(obj, 'userprofile') else None
    phone_number.short_description = 'Phone Number'

    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_staff')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)