from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('w/<str:code>/<slug:name>/', views.public_wishlist, name='public_view'),
    path('all/', views.wishlist_list, name='wishlist_list'),
    path('<int:pk>/', views.wishlist_detail, name='wishlist_detail'),
    path('create/', views.wishlist_create, name='wishlist_create'),
    path('wishlist/<int:pk>/delete/', views.wishlist_delete, name='wishlist_delete'),
    path('<int:pk>/edit_name/', views.wishlist_edit_name, name='wishlist_edit_name'),
    path('<int:wishlist_pk>/item/create/', views.item_create, name='item_create'),
    path('item/<int:pk>/', views.item_detail, name='item_detail'),
    path('item/<int:pk>/edit/', views.item_edit, name='item_edit'),
    path('item/<int:pk>/public/', views.public_item_detail, name='public_item_detail'),
    path('item/<int:pk>/reserve/', views.reserve_item, name='reserve_item'),
    path('item/<int:pk>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('item/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('wishlists/friends/', views.friends_wishlists, name='friends_wishlists'),
    path('wishlist/<int:pk>/edit-image/', views.wishlist_edit_image, name='wishlist_edit_image'),
]