from django.db import models
import os
import uuid
from django.utils.deconstruct import deconstructible
from django.utils import timezone

from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User

# Create your models here.

class Wishlist(models.Model):
    """
    Represents a wishlist created by a user.
    Attributes:
        user (ForeignKey): Owner of the wishlist.
        name (CharField): Name of the wishlist.
        code (SlugField): Unique slug code for public access.
        created_at (DateTimeField): Timestamp of creation.
        image (ImageField): Optional image for the wishlist.
        shared_with (ManyToManyField): Users with whom the wishlist is shared.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlists')
    name = models.CharField(max_length=200, default="My Wishlist")
    code = models.SlugField(max_length=50, editable=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    image = models.ImageField(upload_to='wishlist_images/', blank=True, null=True)
    
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='shared_wishlists',
        blank=True
    )    
    def __str__(self):
        """Return a string representation of the wishlist."""
        return f"{self.user.username}'s wishlist: {self.name}"

    def save(self, *args, **kwargs):
        """
        Override save method to generate a unique code if not set.
        """
        if not self.code:
            base_code = self.user.email.split('@')[0].lower()
            code = base_code
            counter = 1
            while Wishlist.objects.filter(code=code).exists():
                code = f"{base_code}{counter}"
                counter += 1
            self.code = code
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Return the public URL for this wishlist.
        """
        return reverse('wishlist:public_view', args=[self.code, slugify(self.name)])
    
class WishlistShare(models.Model):
    """
    Represents a shared wishlist between users.
    Attributes:
        wishlist (ForeignKey): Wishlist being shared.
        shared_with (ForeignKey): User with whom the wishlist is shared.
        shared_at (DateTimeField): Timestamp of sharing.
    """
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Ensure uniqueness of wishlist-user pair."""
        unique_together = ('wishlist', 'shared_with')
    
@deconstructible
class PathAndRename:
    """
    Callable class for renaming uploaded files to a UUID and storing in a subdirectory.
    Attributes:
        path (str): Subdirectory path to store the file.
    """
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        """
        Generate a unique filename with UUID while preserving the file extension.
        Returns:
            str: New path and filename.
        """
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        return os.path.join(self.path, filename)

path_and_rename = PathAndRename("images/items/")

class Item(models.Model):
    """
    Represents an item in a wishlist.
    Attributes:
        wishlist (ForeignKey): Wishlist to which the item belongs.
        title (CharField): Item title.
        url (URLField): Optional product URL.
        price (DecimalField): Optional price.
        image (ImageField): Optional image.
        description (TextField): Optional description.
        is_reserved (BooleanField): Flag indicating if reserved.
        reserved_by (ForeignKey): User who reserved the item.
        reserved_at (DateTimeField): Timestamp of reservation.
    """
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200)
    url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to=path_and_rename, blank=True, null=True)
    description = models.TextField(blank=True)
    is_reserved = models.BooleanField(default=False)
    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reserved_items'
    )
    reserved_at = models.DateTimeField(null=True, blank=True)
        
    def reserve(self, user):
        """
        Reserve the item for a specific user.
        Args:
            user (User): The user reserving the item.
        Raises:
            ValueError: If the item is already reserved.
        """
        if self.is_reserved:
            raise ValueError("This item is already reserved.")
        self.is_reserved = True
        self.reserved_by = user
        self.save()

    def cancel_reservation(self, user):
        """
        Cancel the reservation for the item.
        Args:
            user (User): The user cancelling the reservation.
        Raises:
            ValueError: If the user is not the one who reserved the item.
        """
        if self.reserved_by != user:
            raise ValueError("You can only cancel your own reservation.")
        self.is_reserved = False
        self.reserved_by = None
        self.save()

    def __str__(self):
        """Return the title of the item."""
        return self.title
