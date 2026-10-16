from django.contrib import admin
from .models import UserCart, UserCartItem

class UserCartItemInline(admin.TabularInline):
    model = UserCartItem
    extra = 0

@admin.register(UserCart)
class UserCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    inlines = [UserCartItemInline]
