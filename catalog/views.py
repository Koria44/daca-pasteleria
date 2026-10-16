from django.views.generic import ListView, DetailView, View
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from .models import Product, Category, AddOn

class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'variants')
        category_slug = self.request.GET.get('categoria')
        search_query = self.request.GET.get('q')
        ordering = self.request.GET.get('orden', 'featured')
        filter_type = self.request.GET.get('filtro')

        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if search_query:
            qs = qs.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query) | Q(short_description__icontains=search_query))
        if filter_type == 'nuevos':
            qs = qs.filter(is_new=True)
        elif filter_type == 'destacados':
            qs = qs.filter(is_featured=True)
        elif filter_type == 'tortas':
            qs = qs.filter(is_cake=True)

        if ordering == 'precio_asc':
            qs = qs.order_by('base_price')
        elif ordering == 'precio_desc':
            qs = qs.order_by('-base_price')
        elif ordering == 'nombre':
            qs = qs.order_by('name')
        else:
            qs = qs.order_by('-is_featured', '-is_new', 'name')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True).order_by('order')
        context['current_category'] = self.request.GET.get('categoria', '')
        context['current_ordering'] = self.request.GET.get('orden', 'featured')
        context['current_filter'] = self.request.GET.get('filtro', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class CategoryDetailView(ProductListView):
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        qs = Product.objects.filter(category=self.category, is_active=True).prefetch_related('images', 'variants')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['current_category'] = self.category.slug
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'variants')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context['active_variants'] = product.variants.filter(is_active=True).order_by('order', 'portions', 'price')
        context['addons'] = AddOn.objects.filter(is_active=True)
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(pk=product.pk).prefetch_related('images')[:4]
        return context


class ProductFilterHTMXView(View):
    def get(self, request, *args, **kwargs):
        view = ProductListView()
        view.request = request
        qs = view.get_queryset()
        categories = Category.objects.filter(is_active=True).order_by('order')
        return render(request, 'catalog/partials/_product_grid.html', {
            'products': qs,
            'categories': categories,
            'current_category': request.GET.get('categoria', ''),
            'current_ordering': request.GET.get('orden', 'featured'),
            'current_filter': request.GET.get('filtro', ''),
            'search_query': request.GET.get('q', ''),
        })
