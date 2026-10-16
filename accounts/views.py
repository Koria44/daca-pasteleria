from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from orders.models import Order
from custom_orders.models import CustomCakeOrder
from .models import UserProfile, Address

class UserLoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:profile')
        return render(request, 'accounts/login.html')

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            try:
                from cart.cart import Cart
                Cart(request).merge_with_user(user)
            except Exception:
                pass
            messages.success(request, f"¡Bienvenido/a de vuelta, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('accounts:profile')
        else:
            messages.error(request, "Usuario o contraseña incorrectos. Por favor verifica tus datos.")
            return render(request, 'accounts/login.html', {'username': username})


class UserRegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:profile')
        return render(request, 'accounts/register.html')

    def post(self, request):
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()

        if not (username and email and password):
            messages.error(request, "Por favor completa todos los campos obligatorios.")
            return render(request, 'accounts/register.html', request.POST)

        if password != password_confirm:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'accounts/register.html', request.POST)

        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return render(request, 'accounts/register.html', request.POST)

        if User.objects.filter(email=email).exists():
            messages.error(request, "El correo electrónico ya está registrado.")
            return render(request, 'accounts/register.html', request.POST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone = phone
        profile.save()

        login(request, user)
        try:
            from cart.cart import Cart
            Cart(request).merge_with_user(user)
        except Exception:
            pass
        messages.success(request, "¡Tu cuenta ha sido creada exitosamente!")
        return redirect('accounts:profile')


class UserLogoutView(View):
    def post(self, request):
        logout(request)
        messages.info(request, "Has cerrado sesión correctamente. ¡Esperamos verte pronto!")
        return redirect('core:home')

    def get(self, request):
        logout(request)
        messages.info(request, "Has cerrado sesión correctamente.")
        return redirect('core:home')


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        custom_orders = CustomCakeOrder.objects.filter(user=request.user).order_by('-created_at')[:5]
        addresses = request.user.saved_addresses.all()

        return render(request, 'accounts/profile.html', {
            'profile': profile,
            'recent_orders': recent_orders,
            'custom_orders': custom_orders,
            'addresses': addresses,
        })

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user = request.user

        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        profile.phone = request.POST.get('phone', profile.phone)
        profile.rut = request.POST.get('rut', profile.rut)
        profile.default_address_street = request.POST.get('default_address_street', profile.default_address_street)
        profile.default_address_details = request.POST.get('default_address_details', profile.default_address_details)
        profile.default_commune = request.POST.get('default_commune', profile.default_commune)
        profile.dietary_preferences = request.POST.get('dietary_preferences', profile.dietary_preferences)
        profile.save()

        messages.success(request, "Datos de perfil actualizados correctamente.")
        return redirect('accounts:profile')


class AddressCreateView(LoginRequiredMixin, View):
    def post(self, request):
        title = request.POST.get('title', 'Casa')
        recipient_name = request.POST.get('recipient_name') or request.user.get_full_name()
        recipient_phone = request.POST.get('recipient_phone') or (request.user.profile.phone if hasattr(request.user, 'profile') else '')
        street = request.POST.get('street')
        details = request.POST.get('details', '')
        commune = request.POST.get('commune', 'La Florida')
        is_default = request.POST.get('is_default') == 'on'

        if street and recipient_name:
            Address.objects.create(
                user=request.user,
                title=title,
                recipient_name=recipient_name,
                recipient_phone=recipient_phone,
                street=street,
                details=details,
                commune=commune,
                is_default=is_default
            )
            messages.success(request, "Dirección guardada exitosamente.")
        else:
            messages.error(request, "Por favor completa la dirección y nombre del destinatario.")

        return redirect('accounts:profile')


class AddressDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        address.delete()
        messages.info(request, "Dirección eliminada.")
        return redirect('accounts:profile')
