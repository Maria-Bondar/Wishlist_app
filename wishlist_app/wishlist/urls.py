from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.home, name='wishlist_list'),
    path('<int:pk>/', views.wishlist_detail, name='wishlist_detail'),
    path('create/', views.wishlist_create, name='wishlist_create'),
    path('<int:wishlist_pk>/item/create/', views.item_create, name='item_create'),
    # path('<int:wishlist_id>/', views.wishlist_view, name='wishlist'),
    # path('item/<int:pk>/', views.item_detail_view, name='item_detail'),
    # path('all/', views.all_wishlists, name='all'),  
    # path('create/', views.create_wishlist, name='create_wishlist'),  
    # path('close/<int:wishlist_id>/', views.close_wishlist, name='close_wishlist'),
]