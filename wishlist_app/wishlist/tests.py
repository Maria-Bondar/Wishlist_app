from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model

from .models import Wishlist, Item
from accounts.models import UserProfile
from .views import wishlist_list, wishlist_detail, item_detail
from accounts.views import profile_view, create_profile
from accounts.models import CustomUser


class ModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
        username="testuser",      
        email="test@example.com",
        password="testpass"
        )
        self.user.is_active = True
        self.user.save()
    
    def test_userprofile_created(self):
        profile, created = UserProfile.objects.get_or_create(user=self.user, defaults={"bio": "Hello bio"})
        self.assertEqual(profile.user.email, "test@example.com")
        self.assertEqual(str(profile), "test@example.com")

    def test_wishlist_and_item(self):
        wishlist = Wishlist.objects.create(name="My Wishlist", user=self.user)
        item = Item.objects.create(wishlist=wishlist, title="Laptop", description="Gaming PC")
        self.assertEqual(str(wishlist), f"{self.user.username}'s wishlist: My Wishlist")
        self.assertEqual(str(item), "Laptop")
        self.assertEqual(item.wishlist.user.email, "test@example.com")


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass"
        )
        self.user.is_active = True
        self.user.save()
        self.wishlist = Wishlist.objects.create(name="Books", user=self.user)
        self.item = Item.objects.create(wishlist=self.wishlist, title="Django book")

    def test_wishlist_list_view(self):
        self.client.login(email="test@example.com", password="testpass")
        url = reverse("wishlist:wishlist_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wishlist/wishlist_list.html")

    def test_wishlist_detail_view(self):
        self.client.login(email="test@example.com", password="testpass")
        url = reverse("wishlist:wishlist_detail", args=[self.wishlist.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Books")

    def test_item_detail_view(self):
        self.client.login(email="test@example.com", password="testpass")
        url = reverse("wishlist:item_detail", args=[self.item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django book")

    def test_profile_requires_login(self):
        profile = UserProfile.objects.create(user=self.user, bio="Test bio")
        url = reverse("accounts:profile", kwargs={"pk": profile.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(email="test@example.com", password="testpass")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class URLTests(TestCase):
    def test_urls_resolve(self):
        self.assertEqual(resolve("/wishlist/item/1/").func, item_detail)
        self.assertEqual(resolve("/wishlist/all/").func, wishlist_list)
        self.assertEqual(resolve("/wishlist/1/").func, wishlist_detail)
        self.assertEqual(resolve("/accounts/profile/1/").func, profile_view)
        self.assertEqual(resolve("/accounts/create_profile/").func, create_profile)