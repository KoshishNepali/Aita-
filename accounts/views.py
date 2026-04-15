from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from functools import wraps
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch
from django.utils import timezone
from datetime import timedelta
import csv

from orders.models import Order, OrderItem
from products.models import Product

from .forms import (
	AdminLoginForm,
	AdminProductForm,
	AdminRegisterForm,
	AdminUserCreateForm,
	AdminUserEditForm,
	LoginForm,
	PasswordChangeForm,
	PaymentMethodForm,
	ProfileEditForm,
	RegisterForm,
)


def _redirect_by_role(role: str):
	if role == 'admin':
		return redirect('/accounts/admin-login/')
	try:
		return redirect('login')
	except NoReverseMatch:
		return redirect('/accounts/login/')


def _redirect_after_login(user):
	if _is_admin_user(user):
		try:
			return redirect('admin_dashboard')
		except NoReverseMatch:
			return redirect('/accounts/admin-dashboard/')
	return redirect('home')


def _is_admin_user(user):
	if not getattr(user, 'is_authenticated', False):
		return False
	if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
		return True
	if hasattr(user, 'is_admin') and user.is_admin:
		return True
	try:
		return user.profile.role == 'admin'
	except (AttributeError, ObjectDoesNotExist):
		return False


def admin_role_required(view_func):
	@login_required
	@wraps(view_func)
	def _wrapped(request, *args, **kwargs):
		if not _is_admin_user(request.user):
			messages.error(request, 'You do not have admin access.')
			return redirect('admin_login')
		return view_func(request, *args, **kwargs)

	return _wrapped


@ensure_csrf_cookie
@never_cache
def register(request):
	if request.method == 'POST':
		form = RegisterForm(request.POST)
		if form.is_valid():
			UserModel = get_user_model()
			role = form.cleaned_data['role']
			user = UserModel.objects.create_user(
				username=form.cleaned_data['username'],
				email=form.cleaned_data['email'],
				password=form.cleaned_data['password'],
			)

			# Keep compatibility with current custom user fields.
			if hasattr(user, 'phone') and not user.phone:
				user.phone = ''
			if hasattr(user, 'address') and not user.address:
				user.address = ''

			# Assume profile role exists, but support direct user role/is_admin fields too.
			try:
				profile = user.profile
				if hasattr(profile, 'role'):
					profile.role = role
					profile.save()
			except (AttributeError, ObjectDoesNotExist):
				pass
			if hasattr(user, 'role'):
				user.role = role
			if hasattr(user, 'is_admin'):
				user.is_admin = role == 'admin'
			if hasattr(user, 'is_staff'):
				user.is_staff = role == 'admin'
			if hasattr(user, 'is_superuser'):
				user.is_superuser = role == 'admin'

			user.save()
			if role == 'admin':
				if request.user.is_authenticated:
					auth_logout(request)
				messages.success(request, 'Admin account created successfully. Please log in.')
				return redirect('/accounts/admin-login/')

			messages.success(request, 'Account created successfully.')
			return _redirect_by_role(role)

		messages.error(request, 'Please correct the errors below.')
	else:
		form = RegisterForm()

	return render(request, 'accounts/register.html', {'form': form})


@ensure_csrf_cookie
@never_cache
def login_view(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			auth_login(request, form.user)
			messages.success(request, 'Logged in successfully.')
			return _redirect_after_login(form.user)
		messages.error(request, 'Please correct the errors below.')
	else:
		form = LoginForm()

	return render(request, 'accounts/login.html', {'form': form})


@ensure_csrf_cookie
@never_cache
def admin_register_view(request):
	if request.method == 'POST':
		form = AdminRegisterForm(request.POST)
		if form.is_valid():
			form.save()
			if request.user.is_authenticated:
				auth_logout(request)
			messages.success(request, 'Admin account created successfully. Please log in.')
			return redirect('/accounts/admin-login/')
		messages.error(request, 'Please correct the errors below.')
	else:
		form = AdminRegisterForm()

	return render(request, 'accounts/admin/admin_register.html', {'form': form})


@ensure_csrf_cookie
@never_cache
def admin_login_view(request):
	if request.user.is_authenticated and _is_admin_user(request.user):
		return redirect('admin_dashboard')

	if request.method == 'POST':
		form = AdminLoginForm(request.POST)
		if form.is_valid():
			if not _is_admin_user(form.user):
				messages.error(request, 'Only admin users can log in here.')
			else:
				auth_login(request, form.user)
				messages.success(request, 'Admin logged in successfully.')
				return redirect('admin_dashboard')
		else:
			messages.error(request, 'Please correct the errors below.')
	else:
		form = AdminLoginForm()

	return render(request, 'accounts/admin/admin_login.html', {'form': form})


@login_required
@never_cache
def logout_view(request):
	auth_logout(request)
	messages.success(request, 'Logged out successfully.')
	return redirect('home')


@login_required
@ensure_csrf_cookie
@never_cache
def profile_view(request):
	orders = Order.objects.filter(user=request.user).order_by('-created_at')
	latest_order = orders.first()
	total_spent = sum((order.total_amount for order in orders), start=0)
	loyalty_points = orders.count() * 75
	active_tab = 'edit-profile'
	payment_method = request.session.get('profile_payment_method', 'esewa')
	payment_method_label = dict(PaymentMethodForm.PAYMENT_METHOD_CHOICES).get(payment_method, 'eSewa')

	def _profile_initials(user):
		full_name = user.get_full_name().strip()
		parts = full_name.split() if full_name else [user.username]
		letters = ''.join(part[0] for part in parts if part)
		return (letters[:2] or 'AM').upper()

	def _display_name(user):
		full_name = user.get_full_name().strip()
		if full_name:
			return full_name
		if user.username:
			return user.username.replace('.', ' ').replace('_', ' ').title()
		return 'Aita Member'

	def _profile_form_initial(user):
		full_name = user.get_full_name().strip() or _display_name(user)
		return {
			'full_name': full_name,
			'email': user.email,
			'phone': getattr(user, 'phone', ''),
			'address': getattr(user, 'address', ''),
		}

	profile_edit_form = ProfileEditForm(initial=_profile_form_initial(request.user))
	payment_form = PaymentMethodForm(initial={'payment_method': payment_method})
	password_form = PasswordChangeForm(request.user)

	if request.method == 'POST':
		action = request.POST.get('profile_action', 'edit-profile')
		active_tab = action
		if action == 'upload-photo':
			photo = request.FILES.get('profile_photo')
			if photo:
				request.user.profile_photo = photo
				request.user.save(update_fields=['profile_photo'])
				messages.success(request, 'Profile photo updated successfully.')
				return redirect('profile')
			messages.error(request, 'Please choose a valid photo to upload.')
		if action == 'edit-profile':
			profile_edit_form = ProfileEditForm(request.POST)
			if profile_edit_form.is_valid():
				profile_edit_form.save(request.user)
				messages.success(request, 'Profile updated successfully.')
				return redirect('profile')
		elif action == 'payment-methods':
			payment_form = PaymentMethodForm(request.POST)
			if payment_form.is_valid():
				request.session['profile_payment_method'] = payment_form.cleaned_data['payment_method']
				request.session.modified = True
				messages.success(request, 'Payment method updated successfully.')
				return redirect('profile')
		elif action == 'account-settings':
			password_form = PasswordChangeForm(request.user, request.POST)
			if password_form.is_valid():
				password_form.save()
				update_session_auth_hash(request, request.user)
				messages.success(request, 'Password changed successfully.')
				return redirect('profile')
		else:
			messages.error(request, 'Please choose a valid profile section.')

	context = {
		'user': request.user,
		'display_name': _display_name(request.user),
		'initials': _profile_initials(request.user),
		'profile_photo': getattr(request.user, 'profile_photo', None),
		'member_since': request.user.date_joined,
		'latest_order': latest_order,
		'orders_count': orders.count(),
		'total_spent': total_spent,
		'loyalty_points': loyalty_points,
		'profile_edit_form': profile_edit_form,
		'payment_form': payment_form,
		'password_form': password_form,
		'active_tab': active_tab,
		'payment_method': payment_method,
		'payment_method_label': payment_method_label,
	}
	return render(request, 'accounts/profile_page.html', context)


@admin_role_required
def admin_dashboard_view(request):
	line_total = ExpressionWrapper(
		F('price') * F('quantity'),
		output_field=DecimalField(max_digits=12, decimal_places=2),
	)

	revenue_mix_qs = OrderItem.objects.filter(
		order__status__in=['pending', 'completed'],
		product__is_available=True,
	).values('product__category__name').annotate(
		revenue=Coalesce(
			Sum(line_total),
			Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
		),
	).order_by('-revenue')[:3]

	mix_items_raw = [
		{
			'category': item['product__category__name'] or 'Uncategorized',
			'revenue': float(item['revenue'] or 0),
		}
		for item in revenue_mix_qs
	]
	total_mix_revenue = sum(item['revenue'] for item in mix_items_raw)

	revenue_mix = []
	for item in mix_items_raw:
		percentage = (item['revenue'] / total_mix_revenue * 100) if total_mix_revenue > 0 else 0
		revenue_mix.append({
			'category': item['category'],
			'revenue': item['revenue'],
			'percentage': round(percentage, 1),
		})

	if revenue_mix:
		top_mix = revenue_mix[0]
		mix_note = (
			f"\"{top_mix['category']} is currently leading with {top_mix['percentage']}% "
			f"of category revenue.\""
		)
	else:
		mix_note = '"No revenue mix data is available yet. Place some orders to see trends."'

	context = {
		'admin_active': 'dashboard',
		'revenue_mix': revenue_mix,
		'mix_note': mix_note,
	}
	return render(request, 'accounts/admin/admin_dashboard.html', context)


@admin_role_required
@never_cache
def admin_dashboard_data_view(request):
	UserModel = get_user_model()

	total_users = UserModel.objects.filter(is_staff=False, is_superuser=False).count()
	total_orders = Order.objects.count()
	total_revenue = Order.objects.aggregate(
		total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)))
	)['total']

	recent_users_qs = UserModel.objects.order_by('-date_joined').values(
		'id', 'username', 'email', 'date_joined'
	)[:5]
	recent_orders_qs = Order.objects.select_related('user').order_by('-created_at')[:5]
	top_products_qs = Product.objects.filter(is_available=True).annotate(
		sold_count=Coalesce(Sum('orderitem__quantity'), Value(0))
	).order_by('-sold_count', '-created_at')[:4]

	recent_users = [
		{
			'id': user['id'],
			'username': user['username'],
			'email': user['email'],
			'joined_at': user['date_joined'].isoformat() if user['date_joined'] else None,
		}
		for user in recent_users_qs
	]

	recent_orders = [
		{
			'id': order.id,
			'customer': order.user.username,
			'status': order.status,
			'payment_status': order.payment_status,
			'amount': float(order.total_amount),
			'created_at': order.created_at.isoformat() if order.created_at else None,
		}
		for order in recent_orders_qs
	]

	recent_activity = [
		{
			'type': 'user',
			'label': f"New user: {user['username']}",
			'timestamp': user['joined_at'],
		}
		for user in recent_users
	] + [
		{
			'type': 'order',
			'label': f"Order #{order['id']} by {order['customer']}",
			'timestamp': order['created_at'],
		}
		for order in recent_orders
	]

	recent_activity.sort(key=lambda item: item.get('timestamp') or '', reverse=True)

	top_products = [
		{
			'id': product.id,
			'name': product.name,
			'price': float(product.base_price),
			'image': product.image_src,
			'sold_count': int(getattr(product, 'sold_count', 0) or 0),
			'tag': 'Trending' if int(getattr(product, 'sold_count', 0) or 0) > 0 else 'New',
		}
		for product in top_products_qs
	]

	return JsonResponse({
		'users': total_users,
		'orders': total_orders,
		'revenue': float(total_revenue),
		'recent_users': recent_users,
		'recent_orders': recent_orders,
		'recent_activity': recent_activity[:8],
		'top_products': top_products,
	})


@admin_role_required
def order_management_view(request):
	latest_orders = Order.objects.select_related('user').order_by('-created_at')[:20]
	context = {
		'admin_active': 'orders',
		'initial_orders': latest_orders,
	}
	return render(request, 'accounts/admin/order_management.html', context)


@admin_role_required
@never_cache
def admin_orders_data_view(request):
	orders_qs = Order.objects.select_related('user').order_by('-created_at')[:20]
	today = timezone.localdate()
	yesterday = today - timedelta(days=1)

	daily_revenue = Order.objects.filter(created_at__date=today).aggregate(
		total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)))
	)['total']
	yesterday_revenue = Order.objects.filter(created_at__date=yesterday).aggregate(
		total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)))
	)['total']

	if float(yesterday_revenue) > 0:
		revenue_change_pct = ((float(daily_revenue) - float(yesterday_revenue)) / float(yesterday_revenue)) * 100
	else:
		revenue_change_pct = 100.0 if float(daily_revenue) > 0 else 0.0

	total_orders_count = Order.objects.count()
	total_items_count = OrderItem.objects.aggregate(total=Coalesce(Sum('quantity'), Value(0)))['total']
	avg_items_per_order = (float(total_items_count) / total_orders_count) if total_orders_count > 0 else 0.0
	avg_prep_time_minutes = round(12 + (avg_items_per_order * 1.8), 1) if total_orders_count > 0 else 0.0

	users_with_orders = Order.objects.values('user_id').distinct().count()
	recurring_users = Order.objects.values('user_id').annotate(order_count=Count('id')).filter(order_count__gte=2).count()
	loyalty_pct = round((recurring_users / users_with_orders) * 100, 1) if users_with_orders > 0 else 0.0

	orders = [
		{
			'order_id': order.id,
			'user': order.user.username,
			'user_email': order.user.email,
			'total_amount': float(order.total_amount),
			'status': order.status,
			'created_at': order.created_at.isoformat() if order.created_at else None,
		}
		for order in orders_qs
	]

	return JsonResponse({
		'orders': orders,
		'stats': {
			'daily_revenue': float(daily_revenue),
			'revenue_change_pct': round(revenue_change_pct, 1),
			'avg_prep_time_minutes': avg_prep_time_minutes,
			'customer_loyalty_pct': loyalty_pct,
		},
	})


@admin_role_required
def user_management_view(request):
	initial_users = get_user_model().objects.order_by('-date_joined')[:10]
	return render(
		request,
		'accounts/admin/user_management.html',
		{
			'admin_active': 'users',
			'initial_users': initial_users,
		},
	)


@admin_role_required
@ensure_csrf_cookie
@never_cache
def admin_user_create_view(request):
	if request.method == 'POST':
		form = AdminUserCreateForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'New user created successfully.')
			return redirect('user_management')
		messages.error(request, 'Please fix the errors below.')
	else:
		form = AdminUserCreateForm()

	context = {
		'admin_active': 'users',
		'form': form,
		'form_mode': 'create',
		'form_title': 'Add New User',
		'form_subtitle': 'Create a user account and assign role permissions.',
		'submit_label': 'Create User',
	}
	return render(request, 'accounts/admin/user_form.html', context)


@admin_role_required
@ensure_csrf_cookie
@never_cache
def admin_user_edit_view(request, pk):
	UserModel = get_user_model()
	user_obj = get_object_or_404(UserModel, pk=pk)

	if request.method == 'POST':
		form = AdminUserEditForm(request.POST, user_instance=user_obj)
		if form.is_valid():
			form.save()
			messages.success(request, f'User "{user_obj.username}" updated successfully.')
			return redirect('user_management')
		messages.error(request, 'Please fix the errors below.')
	else:
		initial_data = {
			'username': user_obj.username,
			'email': user_obj.email,
			'phone': getattr(user_obj, 'phone', ''),
			'address': getattr(user_obj, 'address', ''),
			'role': 'admin' if getattr(user_obj, 'is_staff', False) else 'user',
		}
		form = AdminUserEditForm(initial=initial_data, user_instance=user_obj)

	context = {
		'admin_active': 'users',
		'form': form,
		'form_mode': 'edit',
		'form_title': 'Edit User',
		'form_subtitle': f'Update account details for {user_obj.username}.',
		'submit_label': 'Save Changes',
	}
	return render(request, 'accounts/admin/user_form.html', context)


@admin_role_required
@never_cache
def admin_user_delete_view(request, pk):
	if request.method != 'POST':
		return redirect('user_management')

	UserModel = get_user_model()
	user_obj = get_object_or_404(UserModel, pk=pk)

	if user_obj.pk == request.user.pk:
		messages.error(request, 'You cannot delete your own account while logged in.')
		return redirect('user_management')

	username = user_obj.username
	user_obj.delete()
	messages.success(request, f'User "{username}" deleted successfully.')
	return redirect('user_management')


@admin_role_required
@never_cache
def admin_users_data_view(request):
	UserModel = get_user_model()
	query = (request.GET.get('q') or '').strip()
	role_filter = (request.GET.get('role') or 'all').strip().lower()

	try:
		page = int(request.GET.get('page', 1))
	except (TypeError, ValueError):
		page = 1
	if page < 1:
		page = 1

	try:
		page_size = int(request.GET.get('page_size', 10))
	except (TypeError, ValueError):
		page_size = 10
	if page_size < 5:
		page_size = 5
	if page_size > 50:
		page_size = 50

	users_qs = UserModel.objects.all()
	if query:
		users_qs = users_qs.filter(Q(username__icontains=query) | Q(email__icontains=query))
	if role_filter == 'admin':
		users_qs = users_qs.filter(is_staff=True)
	elif role_filter == 'user':
		users_qs = users_qs.filter(is_staff=False)

	users_qs = users_qs.order_by('-date_joined')
	total_items = users_qs.count()
	total_pages = ((total_items - 1) // page_size) + 1 if total_items else 1
	if page > total_pages:
		page = total_pages

	start_index = (page - 1) * page_size
	end_index = start_index + page_size
	latest_users = users_qs.values(
		'id',
		'username',
		'email',
		'is_staff',
		'date_joined',
		'last_login',
	)[start_index:end_index]

	users = [
		{
			'id': user['id'],
			'username': user['username'],
			'email': user['email'],
			'is_staff': bool(user['is_staff']),
			'date_joined': user['date_joined'].isoformat() if user['date_joined'] else None,
			'last_login': user['last_login'].isoformat() if user['last_login'] else None,
		}
		for user in latest_users
	]

	now = timezone.now()
	active_since = now - timedelta(minutes=15)
	stats = {
		'total_users': UserModel.objects.count(),
		'active_now': UserModel.objects.filter(last_login__gte=active_since).count(),
		'admins': UserModel.objects.filter(is_staff=True).count(),
		'new_today': UserModel.objects.filter(date_joined__date=timezone.localdate()).count(),
	}

	return JsonResponse(
		{
			'users': users,
			'stats': stats,
			'pagination': {
				'page': page,
				'page_size': page_size,
				'total_items': total_items,
				'total_pages': total_pages,
				'has_prev': page > 1,
				'has_next': page < total_pages,
				'start_index': (start_index + 1) if total_items > 0 else 0,
				'end_index': min(end_index, total_items),
			},
		}
	)


@admin_role_required
@never_cache
def admin_users_export_csv_view(request):
	UserModel = get_user_model()
	query = (request.GET.get('q') or '').strip()
	role_filter = (request.GET.get('role') or 'all').strip().lower()

	users_qs = UserModel.objects.all()
	if query:
		users_qs = users_qs.filter(Q(username__icontains=query) | Q(email__icontains=query))
	if role_filter == 'admin':
		users_qs = users_qs.filter(is_staff=True)
	elif role_filter == 'user':
		users_qs = users_qs.filter(is_staff=False)

	users_qs = users_qs.order_by('-date_joined').values(
		'id',
		'username',
		'email',
		'is_staff',
		'date_joined',
		'last_login',
	)

	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="users_export.csv"'

	writer = csv.writer(response)
	writer.writerow(['ID', 'Username', 'Email', 'Role', 'Date Joined', 'Last Login'])

	for user in users_qs:
		writer.writerow(
			[
				user['id'],
				user['username'] or '',
				user['email'] or '',
				'Admin' if user['is_staff'] else 'User',
				user['date_joined'].strftime('%Y-%m-%d %H:%M:%S') if user['date_joined'] else '',
				user['last_login'].strftime('%Y-%m-%d %H:%M:%S') if user['last_login'] else '',
			]
		)

	return response


@admin_role_required
def manage_products_view(request):
	query = (request.GET.get('q') or '').strip()
	all_products_qs = Product.objects.select_related('category')
	products_qs = all_products_qs.order_by('-created_at')
	if query:
		products_qs = products_qs.filter(name__icontains=query)

	context = {
		'admin_active': 'products',
		'query': query,
		'products': products_qs,
		'displayed_products_count': products_qs.count(),
		'total_products': all_products_qs.count(),
		'active_products': all_products_qs.filter(is_available=True).count(),
		'low_inventory_count': all_products_qs.filter(is_available=False).count(),
	}
	return render(request, 'accounts/admin/manage_products.html', context)


@admin_role_required
@ensure_csrf_cookie
@never_cache
def admin_product_create_view(request):
	if request.method == 'POST':
		form = AdminProductForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			messages.success(request, 'Product added successfully.')
			return redirect('manage_products')
		messages.error(request, 'Please fix the errors below.')
	else:
		form = AdminProductForm()

	context = {
		'admin_active': 'products',
		'form': form,
		'form_mode': 'create',
		'form_title': 'Add New Product',
		'form_subtitle': 'Create a menu item for your store.',
		'submit_label': 'Create Product',
	}
	return render(request, 'accounts/admin/product_form.html', context)


@admin_role_required
@ensure_csrf_cookie
@never_cache
def admin_product_edit_view(request, pk):
	product = get_object_or_404(Product, pk=pk)

	if request.method == 'POST':
		form = AdminProductForm(request.POST, request.FILES, instance=product)
		if form.is_valid():
			form.save()
			messages.success(request, 'Product updated successfully.')
			return redirect('manage_products')
		messages.error(request, 'Please fix the errors below.')
	else:
		form = AdminProductForm(instance=product)

	context = {
		'admin_active': 'products',
		'form': form,
		'product': product,
		'form_mode': 'edit',
		'form_title': 'Edit Product',
		'form_subtitle': f'Update details for {product.name}.',
		'submit_label': 'Save Changes',
	}
	return render(request, 'accounts/admin/product_form.html', context)


@admin_role_required
@never_cache
def admin_product_delete_view(request, pk):
	if request.method != 'POST':
		return redirect('manage_products')

	product = get_object_or_404(Product, pk=pk)
	product_name = product.name
	product.delete()
	messages.success(request, f'Product "{product_name}" deleted successfully.')
	return redirect('manage_products')
