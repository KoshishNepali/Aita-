from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from cart.models import Cart, CartItem

from .models import Category, Product


def home(request):
	category_filter = (request.GET.get('category') or 'all').strip().lower()
	if category_filter not in {'all', 'sushi', 'bowls'}:
		category_filter = 'all'

	if category_filter == 'all':
		products = Product.objects.filter(is_available=True).order_by('-created_at')[:4]
	else:
		category_obj = Category.objects.filter(name__iexact=category_filter).first()
		if category_obj:
			products = Product.objects.filter(
				category=category_obj,
				is_available=True
			).order_by('-created_at')[:4]
		else:
			products = Product.objects.filter(is_available=True).order_by('-created_at')[:4]

	context = {
		'products': products,
		'current_category': category_filter,
	}
	return render(request, 'products/home_page.html', context)


def menu_page(request):
	sushi_products = Product.objects.filter(
		is_available=True,
		category__name__iexact='sushi'
	).order_by('-created_at')
	bowl_products = Product.objects.filter(
		is_available=True,
		category__name__iexact='bowls'
	).order_by('-created_at')

	context = {
		'sushi_products': sushi_products,
		'bowl_products': bowl_products,
	}
	return render(request, 'products/menu_page.html', context)


@login_required
def cart_page_view(request):
	current_cart = (
		Cart.objects.filter(user=request.user)
		.prefetch_related('items__product')
		.order_by('-id')
		.first()
	)
	cart_items = []
	total_price = Decimal('0.00')

	if current_cart:
		for item in current_cart.items.all():
			line_total = item.price * item.quantity
			setattr(item, 'line_total', line_total)
			cart_items.append(item)
			total_price += line_total

	delivery_fee = Decimal('5.00') if cart_items else Decimal('0.00')
	service_tax = (total_price * Decimal('0.10')).quantize(Decimal('0.01'))
	grand_total = total_price + delivery_fee + service_tax

	context = {
		'cart_items': cart_items,
		'total_price': total_price,
		'delivery_fee': delivery_fee,
		'service_tax': service_tax,
		'grand_total': grand_total,
	}
	return render(request, 'products/cart_page.html', context)


def product_detail_view(request, pk):
	product = get_object_or_404(Product, id=pk)
	context = {
		'product': product,
	}
	return render(request, 'products/product_detail.html', context)


@login_required
def add_to_cart(request, pk):
	if request.method != 'POST':
		return redirect('product_detail', pk=pk)

	product = get_object_or_404(Product, id=pk, is_available=True)
	selected_option = (request.POST.get('selected_option') or 'Standard').strip() or 'Standard'

	cart = Cart.objects.filter(user=request.user).order_by('-id').first()
	if not cart:
		cart = Cart.objects.create(user=request.user)
	cart_item = CartItem.objects.filter(
		cart=cart,
		product=product,
		selected_option=selected_option,
	).first()

	if cart_item:
		cart_item.quantity += 1
		cart_item.save(update_fields=['quantity'])
	else:
		CartItem.objects.create(
			cart=cart,
			product=product,
			selected_option=selected_option,
			price=product.base_price,
			quantity=1,
		)

	return redirect('cart')


@login_required
def update_cart_item_quantity(request, item_id):
	if request.method != 'POST':
		return redirect('cart')

	item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
	action = (request.POST.get('action') or '').strip().lower()

	if action == 'increase':
		item.quantity += 1
	elif action == 'decrease':
		item.quantity = max(1, item.quantity - 1)

	item.save(update_fields=['quantity'])
	return redirect('cart')


@login_required
def remove_cart_item(request, item_id):
	if request.method != 'POST':
		return redirect('cart')

	item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
	item.delete()
	return redirect('cart')
