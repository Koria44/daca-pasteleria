from django.views.generic import TemplateView
from catalog.models import Category, Product
from core.models import Banner, Testimonial

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banners'] = Banner.objects.filter(is_active=True).order_by('order')
        context['categories'] = Category.objects.filter(is_active=True).order_by('order')[:8]
        context['featured_products'] = Product.objects.filter(is_active=True, is_featured=True).prefetch_related('images', 'variants')[:8]
        context['new_products'] = Product.objects.filter(is_active=True, is_new=True).prefetch_related('images', 'variants')[:8]
        context['testimonials'] = Testimonial.objects.filter(is_active=True).order_by('order')
        return context

class AboutView(TemplateView):
    template_name = 'core/about.html'

class ContactView(TemplateView):
    template_name = 'core/contact.html'

class FaqView(TemplateView):
    template_name = 'core/faq.html'

class TermsView(TemplateView):
    template_name = 'core/terms.html'

class PrivacyView(TemplateView):
    template_name = 'core/privacy.html'

from django.http import HttpResponse

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /panel/",
        "Disallow: /cuentas/",
        "Allow: /",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def sitemap_xml(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    from django.shortcuts import render
    return render(request, 'core/sitemap.xml', {
        'categories': categories,
        'products': products,
        'host': f"{request.scheme}://{request.get_host()}"
    }, content_type='application/xml')
