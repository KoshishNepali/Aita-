from django.urls import path
from . import views

urlpatterns = [
    path('esewa_form/', views.esewa_form, name='esewa_form'),
    path('esewa_verify/<int:order_id>/<int:cart_id>/', views.esewa_verify, name='esewa_verify'),
]

