from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

import os
import uuid
from django.utils.deconstruct import deconstructible

# Create your models here.

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'email'        
    REQUIRED_FIELDS = []           

    def __str__(self):
        return self.email


@deconstructible
class PathAndRename:
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        return os.path.join(self.path, filename)

path_and_rename = PathAndRename("images/profile/")

class Interest(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    TYPE_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    ]

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=LIKE)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(null=True, blank=True)
    likes = models.ManyToManyField(Interest, related_name='likes', blank=True)
    dislikes = models.ManyToManyField(Interest, related_name='dislikes', blank=True)
    profile_pic = models.ImageField(upload_to=path_and_rename, null=True, blank=True)
    facebook = models.CharField(max_length=50, null=True, blank=True)
    twitter = models.CharField(max_length=50, null=True, blank=True)
    instagram = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return str(self.user)
