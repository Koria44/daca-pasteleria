from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Flavor, AddOn

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'alt_text', 'order', 'is_main')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 2
    fields = ('name', 'portions', 'dimensions', 'price', 'stock', 'is_active', 'order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'is_cake', 'is_featured', 'is_new', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'is_featured', 'is_new', 'is_cake')
    list_editable = ('base_price', 'is_featured', 'is_new', 'is_active')
    search_fields = ('name', 'description', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    fieldsets = (
        ('Información Principal', {
            'fields': ('category', 'name', 'slug', 'short_description', 'description', 'base_price')
        }),
        ('Características y Opciones', {
            'fields': ('is_cake', 'is_featured', 'is_new', 'is_active', 'stock', 'preparation_time')
        }),
        ('Información Nutricional y Cuidados', {
            'fields': ('allergens', 'storage_instructions')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Flavor)
class FlavorAdmin(admin.ModelAdmin):
    list_display = ('name', 'flavor_type', 'extra_price', 'is_active')
    list_filter = ('flavor_type', 'is_active')
    search_fields = ('name',)


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
