from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    # path('', views.home, name='wishlist_list'),
    path('w/<str:code>/<slug:name>/', views.public_wishlist, name='public_view'),
    path('all/', views.wishlist_list, name='wishlist_list'),
    path('<int:pk>/', views.wishlist_detail, name='wishlist_detail'),
    path('create/', views.wishlist_create, name='wishlist_create'),
    path('<int:wishlist_pk>/item/create/', views.item_create, name='item_create'),
    # path('item/<int:pk>/', views.item_detail, name='item_detail'),
    path('item/<int:pk>/edit/', views.item_edit, name='item_edit'),
    path('item/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('item/<int:pk>/', views.public_item_detail, name='item_detail'),
]