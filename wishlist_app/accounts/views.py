from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import HttpResponseRedirect
import requests

from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm, Interest, EmailLoginForm, RegisterForm, EditUserForm
from .models import UserProfile, CustomUser

# Create your views here.

def register_view(request):
    """
    Handle user registration.
    Creates a new user, sends an activation email,
    and renders the registration form.
    """
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
                form.add_error('email', 'Unable to send confirmation to this address. Please check your email.')
                return render(request, 'accounts/register.html', {'form': form})
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

def activate_account(request, uidb64, token):
    """
    Activate a user's account.
    Decodes the user ID from the URL and checks the activation token.
    Renders success or invalid activation page.
    """
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
    """
    Handle user login using email.
    Validates the form and logs in the user if credentials are correct.
    """
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
    """Log out the current user and redirect to the login page."""
    logout(request)
    return redirect('accounts:login')

@login_required
def profile_view(request, pk):
    """
    Display a user's profile.
    Args:
        request: HttpRequest object
        pk: Primary key of the UserProfile

    Returns:
        Rendered profile page with context including edit permissions.
    """
    profile = get_object_or_404(UserProfile, pk=pk)
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'can_edit': request.user.is_authenticated and request.user == profile.user,
    })
    
@login_required
def create_profile(request):
    """
    Create a profile for the logged-in user if one does not exist.
    Handles interests (likes/dislikes) and profile picture.
    """
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

@login_required
def edit_profile(request, pk):
    """
    Edit the profile of the logged-in user.
    Handles form submission for user and profile data,
    manages likes and dislikes, and optional profile picture deletion.
    """
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



import urllib.parse

def gerenate_google_oauth_redirect_url():
    """
    Generate the Google OAuth2 authorization redirect URL.
    Returns:
        str: URL to redirect user for Google authentication.
    """
    query_parameters = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": "http://localhost:8000/accounts/auth/google/",
        "response_type": "code", 
        "scope": "openid profile email",
        "prompt": "consent",
    }
    
    query_string = urllib.parse.urlencode(query_parameters, quote_via=urllib.parse.quote)
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    
    final_url = f"{base_url}?{query_string}"
    
    
    print("=== GOOGLE OAUTH DEBUG ===")
    print("Generated redirect URL:", final_url)
    print("==========================")
    
    return final_url

def google_oauth_url(request):
    """
    Handle Google OAuth2 login flow.
    Redirects to Google for authorization or processes the returned code.
    Args:
        request: HttpRequest object
    Returns:
        HttpResponseRedirect to the appropriate page based on success or failure.
    """
    code = request.GET.get("code")
    error = request.GET.get("error")
    
    if error:
        return HttpResponseRedirect("/accounts/login/?error=oauth_denied")
    
    if not code:
        url = gerenate_google_oauth_redirect_url()
        return HttpResponseRedirect(url)
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": "http://localhost:8000/accounts/auth/google/",
        "grant_type": "authorization_code",
    }

    # Get token
    try:
        r = requests.post(token_url, data=data)
        token_response = r.json()
        access_token = token_response.get("access_token")

        if not access_token:
            return HttpResponseRedirect("/accounts/login/")  # або сторінка з помилкою

        #Get information about user
        user_info = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        email = user_info.get("email")
        name = user_info.get("name")

        if not email:
            return HttpResponseRedirect("/accounts/login/")

        # Create or get user
        user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={"username": email, "first_name": name}
        )
        
        login(request, user)
        return HttpResponseRedirect("/")
    
    except requests.exceptions.RequestException as e:
        print("Request error:", e)
        return HttpResponseRedirect("/accounts/login/?error=request_failed")
    except Exception as e:
        print("Unexpected error:", e)
        return HttpResponseRedirect("/accounts/login/?error=unexpected")
    