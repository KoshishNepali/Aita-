from django.urls import path

from . import views


urlpatterns = [
	path('checkout/', views.checkout_page_view, name='checkout'),
]
