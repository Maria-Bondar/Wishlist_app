from django import forms
from .models import Wishlist, Item

class WishlistForm(forms.ModelForm):
    class Meta:
        model = Wishlist
        fields = ['name']
        
class WishlistImageForm(forms.ModelForm):
    class Meta:
        model = Wishlist
        fields = ['image']

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'url', 'price', 'image', 'description']