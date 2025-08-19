from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser, UserProfile, Interest

class AccountsModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass'
        )
        self.user.is_active = True
        self.user.save()

    def test_userprofile_creation(self):
        profile = UserProfile.objects.create(user=self.user, bio="Hello")
        self.assertEqual(profile.user.email, 'test@example.com')
        self.assertEqual(profile.bio, "Hello")

    def test_interest_creation(self):
        like = Interest.objects.create(name="Football", type="like")
        dislike = Interest.objects.create(name="Spinach", type="dislike")
        self.assertEqual(str(like), "Football")
        self.assertEqual(like.type, "like")
        self.assertEqual(str(dislike), "Spinach")
        self.assertEqual(dislike.type, "dislike")

class AccountsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass'
        )
        self.profile = UserProfile.objects.create(user=self.user, bio="Bio test")
        self.user.is_active = True
        self.user.save()

    def test_register_view_get(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_login_view_get(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_logout_view_redirects(self):
        self.client.login(email='test@example.com', password='testpass')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_profile_requires_login(self):
        url = reverse('accounts:profile', kwargs={'pk': self.profile.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(email='test@example.com', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_edit_profile_view(self):
        url = reverse('accounts:edit_profile', kwargs={'pk': self.profile.pk})
        self.client.login(email='test@example.com', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/edit_profile.html')

    def test_create_profile_redirect_if_exists(self):
        self.client.login(email='test@example.com', password='testpass')
        url = reverse('accounts:create_profile')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('accounts:edit_profile', kwargs={'pk': self.profile.pk}))


class AccountsViewPOSTTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass'
        )
        self.user.is_active = True
        self.user.save()
        self.client.login(email='test@example.com', password='testpass')

        self.like = Interest.objects.create(name='Football', type='like')
        self.dislike = Interest.objects.create(name='Spinach', type='dislike')

    def test_create_profile_post(self):
        url = reverse('accounts:create_profile')
        data = {
            'bio': 'My new bio',
            'likes_existing': [self.like.id],
            'dislikes_existing': [self.dislike.id],
            'likes_new': ['Basketball'],
            'dislikes_new': ['Broccoli'],
        }
        response = self.client.post(url, data)
        profile = UserProfile.objects.get(user=self.user)
        self.assertRedirects(response, reverse('accounts:profile', kwargs={'pk': profile.pk}))
        self.assertIn(self.like, profile.likes.all())
        self.assertIn(self.dislike, profile.dislikes.all())
        self.assertTrue(profile.likes.filter(name='🎁 Basketball').exists())
        self.assertTrue(profile.dislikes.filter(name='🚫 Broccoli').exists())

    def test_edit_profile_post(self):
        profile = UserProfile.objects.create(user=self.user, bio='Old bio')
        url = reverse('accounts:edit_profile', kwargs={'pk': profile.pk})
        data = {
            'bio': 'Updated bio',
            'likes_existing': [self.like.id],
            'dislikes_existing': [self.dislike.id],
            'likes_new': ['Tennis'],
            'dislikes_new': ['Cabbage'],
        }
        response = self.client.post(url, data)
        profile.refresh_from_db()
        self.assertRedirects(response, reverse('accounts:profile', kwargs={'pk': profile.pk}))
        self.assertIn(self.like, profile.likes.all())
        self.assertIn(self.dislike, profile.dislikes.all())
        self.assertTrue(profile.likes.filter(name='🎁 Tennis').exists())
        self.assertTrue(profile.dislikes.filter(name='🚫 Cabbage').exists())
        self.assertEqual(profile.bio, 'Updated bio')