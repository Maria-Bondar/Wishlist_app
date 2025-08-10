from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .models import CustomUser
from .forms import RegisterForm, EmailLoginForm

# Create your views here.
def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('wishlist:home')
    else:
        form = EmailLoginForm()
    return render(request, 'accounts/login.html', {'form': form})