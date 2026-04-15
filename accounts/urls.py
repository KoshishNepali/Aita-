from django.urls import path

from . import views


urlpatterns = [
	path('register/', views.register, name='register'),
	path('login/', views.login_view, name='login'),
	path('logout/', views.logout_view, name='logout'),
	path('admin-register/', views.admin_register_view, name='admin_register'),
	path('admin-login/', views.admin_login_view, name='admin_login'),
	path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
	path('admin-dashboard-data/', views.admin_dashboard_data_view, name='admin_dashboard_data'),
	path('admin-orders-data/', views.admin_orders_data_view, name='admin_orders_data'),
	path('admin-users-data/', views.admin_users_data_view, name='admin_users_data'),
	path('admin-users-export-csv/', views.admin_users_export_csv_view, name='admin_users_export_csv'),
	path('profile/', views.profile_view, name='profile'),
	path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard_legacy'),
	path('admin/orders/', views.order_management_view, name='order_management'),
	path('admin/users/', views.user_management_view, name='user_management'),
	path('admin/users/add/', views.admin_user_create_view, name='admin_user_create'),
	path('admin/users/<int:pk>/edit/', views.admin_user_edit_view, name='admin_user_edit'),
	path('admin/users/<int:pk>/delete/', views.admin_user_delete_view, name='admin_user_delete'),
	path('admin/products/', views.manage_products_view, name='manage_products'),
	path('admin/products/add/', views.admin_product_create_view, name='admin_product_create'),
	path('admin/products/<int:pk>/edit/', views.admin_product_edit_view, name='admin_product_edit'),
	path('admin/products/<int:pk>/delete/', views.admin_product_delete_view, name='admin_product_delete'),
]
