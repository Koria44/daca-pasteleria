from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('nosotros/', views.AboutView.as_view(), name='about'),
    path('contacto/', views.ContactView.as_view(), name='contact'),
    path('preguntas-frecuentes/', views.FaqView.as_view(), name='faq'),
    path('terminos-y-condiciones/', views.TermsView.as_view(), name='terms'),
    path('politica-de-privacidad/', views.PrivacyView.as_view(), name='privacy'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
]
