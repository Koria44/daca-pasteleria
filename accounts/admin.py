from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Address

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Cliente'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_phone')

    def get_phone(self, instance):
        if hasattr(instance, 'profile'):
            return instance.profile.phone
        return ''
    get_phone.short_description = 'Teléfono'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'recipient_name', 'street', 'commune', 'is_default')
    list_filter = ('commune', 'is_default')
    search_fields = ('user__username', 'recipient_name', 'street')
