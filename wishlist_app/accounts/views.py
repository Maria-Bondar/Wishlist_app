from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm, Interest
from .models import UserProfile

from .forms import EmailLoginForm, RegisterForm

# Create your views here.

def register_view(request):
    if request.method == 'POST':
        print("here")
        form = RegisterForm(request.POST)
        if form.is_valid():
            print("Success register")
            form.save()
            return redirect('home')
    else:
        print("Empty register")
        form = RegisterForm() 
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            print("Success login")
            login(request, user)
            return redirect('home')
    else:
        print("Empty login")
        form = EmailLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def profile_view(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    return render(request, 'accounts/profile.html', {
        'profile': profile,
    })

@login_required
def edit_profile(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            profile.likes.clear()
            profile.dislikes.clear()

            # Отримати списки з форми
            likes_list = request.POST.getlist('likes')
            dislikes_list = request.POST.getlist('dislikes')

            for name in likes_list:
                if name.strip():
                    interest, _ = Interest.objects.get_or_create(name=name.strip())
                    profile.likes.add(interest)

            for name in dislikes_list:
                if name.strip():
                    interest, _ = Interest.objects.get_or_create(name=name.strip())
                    profile.dislikes.add(interest)
            return redirect('accounts:profile', pk=profile.pk)
        else:
            print(form.errors)
    else:
        print("method not post")
        form = UserProfileForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'likes': profile.likes.all(),
        'dislikes': profile.dislikes.all(),
        })

def create_profile(request):
    user = request.user
    
    # Перевірка, чи профіль вже є
    if hasattr(user, 'userprofile'):
        # Можна перенаправити на редагування профілю або профіль
        return redirect('accounts:edit_profile', pk=profile.pk)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            # Обробка likes
            likes_input = request.POST.getlist('likes')
            for name in likes_input:
                interest, _ = Interest.objects.get_or_create(name=name)
                profile.likes.add(interest)

            # Обробка dislikes
            dislikes_input = request.POST.getlist('dislikes')
            for name in dislikes_input:
                interest, _ = Interest.objects.get_or_create(name=name)
                profile.dislikes.add(interest)

            return redirect('accounts:profile', pk=profile.pk)
    else:
        form = UserProfileForm()
    return render(request, 'accounts/create_profile.html', {'form': form})


