from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings

from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm, Interest, EmailLoginForm, RegisterForm, EditUserForm
from .models import UserProfile, CustomUser

# Create your views here.

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()

            # Send a letter for confirmation
            current_site = get_current_site(request)
            domain = current_site.domain

            mail_subject = 'Activate Your Account'
            message = render_to_string('accounts/account_activation_email.html', {
                'user': user,
                'domain': domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })

            email = EmailMessage(mail_subject, message, settings.EMAIL_HOST_USER, [user.email])
            email.content_subtype = 'html'  
            try:
                email.send(fail_silently=False)
                return render(request, 'accounts/registration_pending.html')
            except Exception as e:
                form.add_error('email', 'Не вдалося надіслати підтвердження на цю адресу. Будь ласка, перевірте email.')
                return render(request, 'accounts/register.html', {'form': form})
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'accounts/activation_success.html')
    else:
        return render(request, 'accounts/activation_invalid.html')


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
        'can_edit': request.user.is_authenticated and request.user == profile.user,
    })

@login_required
def edit_profile(request, pk):
    user_profile = get_object_or_404(UserProfile, pk=pk)
    user_form = EditUserForm(request.POST or None, instance=request.user)
    profile_form = UserProfileForm(request.POST or None, request.FILES or None, instance=user_profile)

    # Divide interests by type
    all_interests_likes = Interest.objects.filter(type='like')
    all_interests_dislikes = Interest.objects.filter(type='dislike')

    if request.method == "POST":
        if user_form.is_valid() and profile_form.is_valid():
            if request.POST.get('clear_photo') == 'true':
                profile_form.instance.profile_pic.delete(save=False)
                profile_form.instance.profile_pic = None
                
            user_form.save()
            profile_form.save()
            
            LIKE_EMOJI = "🎁"
            DISLIKE_EMOJI = "🚫"

            # Likes
            likes_existing_ids = request.POST.getlist('likes_existing')
            likes_objs = list(Interest.objects.filter(id__in=likes_existing_ids))
            for name in request.POST.getlist('likes_new'):
                if name:
                    name_with_emoji = f"{LIKE_EMOJI} {name.strip()}"
                    interest, _ = Interest.objects.get_or_create(name=name_with_emoji, type='like')
                    likes_objs.append(interest)

            #Dislikes
            dislikes_existing_ids = request.POST.getlist('dislikes_existing')
            dislikes_objs = list(Interest.objects.filter(id__in=dislikes_existing_ids))
            for name in request.POST.getlist('dislikes_new'):
                if name:
                    name_with_emoji = f"{DISLIKE_EMOJI} {name.strip()}"
                    interest, _ = Interest.objects.get_or_create(name=name_with_emoji, type='dislike')
                    dislikes_objs.append(interest)

            dislikes_objs = [d for d in dislikes_objs if d not in likes_objs]

            user_profile.likes.set(likes_objs)
            user_profile.dislikes.set(dislikes_objs)

            return redirect('accounts:profile', pk=user_profile.pk)

    # Forming options for selection
    likes_choices = all_interests_likes.exclude(id__in=user_profile.dislikes.all())
    dislikes_choices = all_interests_dislikes.exclude(id__in=user_profile.likes.all())

    context = {
        'user_profile': user_profile,
        'user_form': user_form,
        'profile_form': profile_form,
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
            
            LIKE_EMOJI = "🎁"
            DISLIKE_EMOJI = "🚫"

            # Likes
            likes_existing_ids = request.POST.getlist('likes_existing')
            likes_objs = list(Interest.objects.filter(id__in=likes_existing_ids))
            for name in request.POST.getlist('likes_new'):
                if name:
                    name_with_emoji = f"{LIKE_EMOJI} {name.strip()}"
                    interest, _ = Interest.objects.get_or_create(name=name_with_emoji, defaults={'type': 'like'})
                    likes_objs.append(interest)

            # Dislikes
            dislikes_existing_ids = request.POST.getlist('dislikes_existing')
            dislikes_objs = list(Interest.objects.filter(id__in=dislikes_existing_ids))
            for name in request.POST.getlist('dislikes_new'):
                if name:
                    name_with_emoji = f"{DISLIKE_EMOJI} {name.strip()}"
                    interest, _ = Interest.objects.get_or_create(name=name_with_emoji, defaults={'type': 'dislike'})
                    dislikes_objs.append(interest)

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