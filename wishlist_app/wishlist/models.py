from django.db import models
import os
import uuid
from django.utils.deconstruct import deconstructible

from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify

# Create your models here.

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlists')
    name = models.CharField(max_length=200, default="My Wishlist")
    
    code = models.SlugField(max_length=50, editable=False, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.name}"
    

    def save(self, *args, **kwargs):
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
        return reverse('wishlist:public_view', args=[self.code, slugify(self.name)])
    
@deconstructible
class PathAndRename:
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        return os.path.join(self.path, filename)

path_and_rename = PathAndRename("images/items/")

class Item(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200)
    url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to=path_and_rename, blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title
