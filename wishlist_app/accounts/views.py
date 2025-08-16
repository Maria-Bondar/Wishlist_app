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
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = RegisterForm() 
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
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
    user_profile = get_object_or_404(UserProfile, pk=pk)

    # Розділяємо інтереси за типом
    all_interests_likes = Interest.objects.filter(type='like')
    all_interests_dislikes = Interest.objects.filter(type='dislike')
    print("Likes:", all_interests_likes)
    print("Dislikes:", all_interests_dislikes)

    if request.method == "POST":
        likes_existing_ids = request.POST.getlist('likes_existing')
        dislikes_existing_ids = request.POST.getlist('dislikes_existing')

        likes_new_names = request.POST.getlist('likes_new')
        dislikes_new_names = request.POST.getlist('dislikes_new')

        # Нові лайки
        likes_objs = list(Interest.objects.filter(id__in=likes_existing_ids))
        for name in likes_new_names:
            name = name.strip()
            if name:
                interest, _ = Interest.objects.get_or_create(name=name, type='like')
                likes_objs.append(interest)

        # Нові дизлайки
        dislikes_objs = list(Interest.objects.filter(id__in=dislikes_existing_ids))
        for name in dislikes_new_names:
            name = name.strip()
            if name:
                interest, _ = Interest.objects.get_or_create(name=name, type='dislike')
                dislikes_objs.append(interest)

        # Виключаємо перетини
        dislikes_objs = [d for d in dislikes_objs if d not in likes_objs]

        user_profile.likes.set(likes_objs)
        user_profile.dislikes.set(dislikes_objs)

        user_profile.bio = request.POST.get('bio', user_profile.bio)
        if 'profile_pic' in request.FILES:
            user_profile.profile_pic = request.FILES['profile_pic']
        user_profile.save()

        return redirect('accounts:profile', pk=user_profile.pk)

    # Формуємо варіанти для вибору
    likes_choices = all_interests_likes.exclude(id__in=user_profile.dislikes.all())
    dislikes_choices = all_interests_dislikes.exclude(id__in=user_profile.likes.all())

    context = {
        'user_profile': user_profile,
        'all_interests_likes': likes_choices,
        'all_interests_dislikes': dislikes_choices,
        'new_likes': [i.name for i in user_profile.likes.all() if i not in likes_choices],
        'new_dislikes': [i.name for i in user_profile.dislikes.all() if i not in dislikes_choices],
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def create_profile(request):
    user = request.user

    if hasattr(user, 'userprofile'):
        return redirect('accounts:edit_profile', pk=user.userprofile.pk)

    all_likes = Interest.objects.filter(type='like')
    all_dislikes = Interest.objects.filter(type='dislike')

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()

            # Лайки
            likes_existing_ids = request.POST.getlist('likes_existing')
            likes_objs = list(Interest.objects.filter(id__in=likes_existing_ids))
            for name in request.POST.getlist('likes_new'):
                name = name.strip()
                if name:
                    interest, _ = Interest.objects.get_or_create(name=name, defaults={'type': 'like'})
                    likes_objs.append(interest)

            # Дизлайки
            dislikes_existing_ids = request.POST.getlist('dislikes_existing')
            dislikes_objs = list(Interest.objects.filter(id__in=dislikes_existing_ids))
            for name in request.POST.getlist('dislikes_new'):
                name = name.strip()
                if name:
                    interest, _ = Interest.objects.get_or_create(name=name, defaults={'type': 'dislike'})
                    dislikes_objs.append(interest)

            # Виключаємо перетини
            dislikes_objs = [d for d in dislikes_objs if d not in likes_objs]

            profile.likes.set(likes_objs)
            profile.dislikes.set(dislikes_objs)

            return redirect('accounts:profile', pk=profile.pk)
    else:
        form = UserProfileForm()

    context = {
        'form': form,
        'all_interests_likes': all_likes,
        'all_interests_dislikes': all_dislikes,
        'user_profile': None,
        'new_likes': [],
        'new_dislikes': []
    }

    return render(request, 'accounts/create_profile.html', context)