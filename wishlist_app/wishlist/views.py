from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import re
import uuid
import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.http import HttpResponseForbidden

from .forms import WishlistForm, ItemForm, WishlistImageForm
from .models import Item, Wishlist, WishlistShare


# Create your views here.

@login_required
def home(request):
    """
    Render the home page showing all wishlists of the logged-in user.
    """
    wishlists = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist/wishlist_list.html', {'wishlists': wishlists})

@login_required
def wishlist_list(request):
    """
    Render a list of wishlists for the logged-in user, ordered by creation date.
    """
    wishlists = Wishlist.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'wishlist/wishlist_list.html', {'wishlists': wishlists})

@login_required
def public_wishlist(request, code, name):
    """
    Render a public view of a wishlist by its unique code.
    If the user is logged in and not the owner, record a WishlistShare.
    
    Args:
        code (str): Unique code identifying the wishlist.
        name (str): Name of the wishlist (not used for query, only for URL).
    """
    wishlist = get_object_or_404(Wishlist, code=code)
    
    is_owner = request.user.is_authenticated and request.user == wishlist.user

    if request.user.is_authenticated and not is_owner:
        WishlistShare.objects.get_or_create(
            wishlist=wishlist,
            shared_with=request.user
        )

    return render(
        request,
        'wishlist/public_view.html',
        {
            'wishlist': wishlist,
            'is_owner': is_owner
        }
    )

@login_required
def wishlist_detail(request, pk):
    """
    Render the detail view of a wishlist for its owner.
    Args:
        pk (int): Primary key of the wishlist.
    """
    wishlist = get_object_or_404(Wishlist, pk=pk)
    is_owner = wishlist.user == request.user
    return render(
        request,
        'wishlist/wishlist_detail.html',
        {
            'wishlist': wishlist,
            'is_owner': is_owner
        }
    )

@login_required
def wishlist_create(request):
    """
    Handle creation of a new wishlist by the logged-in user.
    Renders form and saves on POST.
    """
    if request.method == 'POST':
        form = WishlistForm(request.POST)
        if form.is_valid():
            wishlist = form.save(commit=False)
            wishlist.user = request.user
            wishlist.save()
            return redirect('wishlist:wishlist_list')
    else:
        form = WishlistForm()
    return render(request, 'wishlist/wishlist_form.html', {'form': form})


@login_required
def wishlist_delete(request, pk):
    """
    Handle deletion of a wishlist by its owner.
    Args:
        pk (int): Primary key of the wishlist to delete.
    """
    wishlist = get_object_or_404(Wishlist, pk=pk, user=request.user)

    if request.method == "POST":
        wishlist.delete()
        messages.success(request, f"Wishlist '{wishlist.name}' was deleted.")
        return redirect('wishlist:wishlist_list') 
    return render(request, 'wishlist/wishlist_confirm_delete.html', {'wishlist': wishlist})

def scrape_product_data(url):
    """
    Scrape product data from a given URL.
    Args:
        url (str): URL of the product page.
    Returns:
        dict: Dictionary containing 'title', 'price', and 'image_url'.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # ===== Title =====
        title_tag = soup.find('h1') 
        if not title_tag: 
            title_tag = soup.find('h1', class_='product-title')
        title = title_tag.get_text(strip=True) if title_tag else ''

        # ===== Price =====
        prices = []
        for tag in soup.find_all(class_=re.compile(r'price', re.I)):
            text = tag.get_text(strip=True)
            match = re.search(r'([\d\s,.]+)\s*(UAH|USD|грн|₴|$)', text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(' ', '').replace(',', '.')
                try:
                    val = float(price_str)
                    if val > 0:
                        prices.append(val)
                except ValueError:
                    continue

        if prices:
            price = max(prices)
        else:
            price = None

        # ===== Image =====
        img_tag = soup.find('meta', property='og:image')
        image_url = img_tag['content'] if img_tag else ''
        print("DEBUG image_url:", image_url)

        return {
            'title': title,
            'price': price,
            'image_url': image_url,
        }
    except Exception as e:
        print('Scrape error:', e)
        return {}

@login_required
def item_create(request, wishlist_pk):
    """
    Create a new item for a wishlist.
    If a URL is provided, attempt to scrape product data and image.
    Args:
        wishlist_pk (int): Primary key of the wishlist to add the item to.
    """
    wishlist = get_object_or_404(Wishlist, pk=wishlist_pk, user=request.user)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.wishlist = wishlist

            if item.url:
                
                data = scrape_product_data(item.url)

                if data.get('title'):
                    item.title = data['title']
                if data.get('price') is not None:
                    item.price = data['price']
                if data.get('description'):
                    item.description = data['description']

                if data.get('image_url'):
                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0",
                            "Referer": item.url
                        }
                        img_resp = requests.get(data['image_url'], headers=headers, stream=True, timeout=10)
                        img_resp.raise_for_status()
                        file_name = f"{uuid.uuid4().hex}.jpg"
                        item.image.save(file_name, ContentFile(img_resp.content), save=False)
                    except Exception as e:
                        print(f"Image download error: {e}")

            item.save()
            return redirect('wishlist:wishlist_detail', pk=wishlist.pk)
    else:
        form = ItemForm()

    return render(request, 'wishlist/item_form.html', {'form': form, 'wishlist': wishlist})


def public_item_detail(request, pk):
    """
    Render the public detail view of an item.
    Args:
        pk (int): Primary key of the item.
    Returns:
        HttpResponse: Rendered template with item details.
    """
    item = get_object_or_404(Item, pk=pk)
    wishlist = item.wishlist  

    return render(request, 'wishlist/public_item_detail.html', {
        'item': item,
        'wishlist': wishlist,
        'is_owner': request.user.is_authenticated and request.user == wishlist.user
    })
    

def item_edit(request, pk):
    """
    Edit an existing item. If the URL has changed, scrape product data and update image.
    Args:
        pk (int): Primary key of the item to edit.
    Returns:
        HttpResponse: Rendered template with edit form or redirects to item detail on success.
    """
    item = get_object_or_404(Item, pk=pk)

    if request.method == "POST":
        old_url = item.url 
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save(commit=False)

            if item.url and item.url != old_url:
                data = scrape_product_data(item.url)

                if data.get('title'):
                    item.title = data['title']
                if data.get('price') is not None:
                    item.price = data['price']
                if data.get('description'):
                    item.description = data['description']

                if data.get('image_url'):
                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0",
                            "Referer": item.url
                        }
                        img_resp = requests.get(data['image_url'], headers=headers, stream=True, timeout=10)
                        img_resp.raise_for_status()
                        file_name = f"{uuid.uuid4().hex}.jpg"
                        item.image.save(file_name, ContentFile(img_resp.content), save=False)
                    except Exception as e:
                        print(f"Image download error: {e}")

            item.save()
            return redirect('wishlist:item_detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)

    return render(request, 'wishlist/item_edit.html', {'form': form, 'item': item})

@login_required
def item_detail(request, pk):
    """
    Render the detail view of an item for the owner.
    Redirect to public view if user is not the owner.
    Args:
        pk (int): Primary key of the item.
    Returns:
        HttpResponse: Rendered template with item details or redirect to public item view.
    """
    item = get_object_or_404(Item, pk=pk)
    if item.wishlist.user != request.user:
        return redirect('wishlist:public_item_detail', pk=item.pk)
    return render(request, 'wishlist/item_detail.html', {'item': item})

@login_required
def item_delete(request, pk):
    """
    Delete an item if the user is the owner of the wishlist.
    Args:
        pk (int): Primary key of the item.
    Returns:
        HttpResponse: Redirect to wishlist detail on deletion or render confirmation template.
    """
    item = get_object_or_404(Item, pk=pk)
    if item.wishlist.user != request.user:
        return HttpResponseForbidden("You can't delete this item.")
    if request.method == 'POST':
        wishlist_pk = item.wishlist.pk
        item.delete()
        return redirect('wishlist:wishlist_detail', pk=wishlist_pk)
    return render(request, 'wishlist/item_confirm_delete.html', {'item': item})


@login_required
def reserve_item(request, pk):
    """
    Reserve an item for the logged-in user if not the owner.
    Args:
        pk (int): Primary key of the item to reserve.
    Returns:
        HttpResponse: Redirect to public item detail with success/error message or render confirmation template.
    """
    item = get_object_or_404(Item, pk=pk)

    if item.wishlist.user == request.user:
        messages.error(request, "You cannot reserve your own gifts.")
        return redirect('wishlist:public_item_detail', pk=item.pk)

    if request.method == "POST":
        try:
            item.reserve(request.user)
            messages.success(request, f"You reserved a gift: {item.title}")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('wishlist:public_item_detail', pk=item.pk)

    return render(request, 'wishlist/item_confirm_reserve.html', {'item': item})

@login_required
def cancel_reservation(request, pk):
    """
    Cancel a reservation of an item for the logged-in user.
    Args:
        pk (int): Primary key of the item to cancel reservation.
    Returns:
        HttpResponse: Redirect to public item detail with success/error message or render confirmation template.
    """
    item = get_object_or_404(Item, pk=pk)

    if request.method == "POST":
        try:
            item.cancel_reservation(request.user)
            messages.success(request, f"You cancelled the reservation for: {item.title}")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('wishlist:public_item_detail', pk=item.pk)

    return render(request, 'wishlist/item_confirm_cancel.html', {'item': item})

@login_required
def friends_wishlists(request):
    """
    Render a list of wishlists shared with the logged-in user by friends.
    Returns:
        HttpResponse: Rendered template with friends' wishlists.
    """
    wishlists = Wishlist.objects.filter(
        shares__shared_with=request.user
    ).distinct()  
    return render(request, 'wishlist/friends_wishlists.html', {'wishlists': wishlists})


@login_required
def wishlist_edit_image(request, pk):
    """
    Edit the image of a wishlist. Supports clearing the image.
    Args:
        pk (int): Primary key of the wishlist to edit.
    Returns:
        HttpResponse: Rendered template with image edit form or redirect to wishlist detail.
    """
    wishlist = get_object_or_404(Wishlist, pk=pk, user=request.user)

    if request.method == 'POST':
        form = WishlistImageForm(request.POST, request.FILES, instance=wishlist)
        if form.is_valid():
            if request.POST.get('clear_image') == 'true':
                wishlist.image.delete(save=False)
                wishlist.image = None
            wishlist = form.save(commit=False)
            wishlist.save()
            return redirect('wishlist:wishlist_detail', pk=wishlist.pk)
    else:
        form = WishlistImageForm(instance=wishlist)

    return render(request, 'wishlist/wishlist_edit_image.html', {'form': form, 'wishlist': wishlist})


@login_required
def wishlist_edit_name(request, pk):
    """
    Edit the name of a wishlist.
    Args:
        pk (int): Primary key of the wishlist to edit.
    Returns:
        HttpResponse: Redirect to wishlist detail page after name change.
    """
    wishlist = get_object_or_404(Wishlist, pk=pk, user=request.user)

    if request.method == "POST":
        new_name = request.POST.get('name', '').strip()
        if new_name:
            wishlist.name = new_name
            wishlist.save()
    return redirect('wishlist:wishlist_detail', pk=wishlist.pk)