from django import forms
from .models import Wishlist, Item

class WishlistForm(forms.ModelForm):
    """Form for creating or editing a wishlist."""
    class Meta:
        model = Wishlist
        fields = ['name']
        
class WishlistImageForm(forms.ModelForm):
    """Form for editing the image of a wishlist."""
    class Meta:
        model = Wishlist
        fields = ['image']

class ItemForm(forms.ModelForm):
    """Form for creating or editing an item in a wishlist."""
    class Meta:
        model = Item
        fields = ['title', 'url', 'price', 'image', 'description']