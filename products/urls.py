from django.urls import path

from . import views


urlpatterns = [
	path('', views.home, name='home'),
	path('menu/', views.menu_page, name='menu'),
	path('cart/', views.cart_page_view, name='cart'),
	path('cart/item/<int:item_id>/quantity/', views.update_cart_item_quantity, name='update_cart_item_quantity'),
	path('cart/item/<int:item_id>/remove/', views.remove_cart_item, name='remove_cart_item'),
	path('product/<int:pk>/', views.product_detail_view, name='product_detail'),
	path('product/<int:pk>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
]
