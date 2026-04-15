from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from orders.models import Order, OrderItem

from .models import Cart, CartItem


@login_required
def checkout_page_view(request):
	current_cart = Cart.objects.filter(user=request.user).order_by('-id').first()
	cart_queryset = (
		CartItem.objects.filter(cart=current_cart)
		.select_related('product', 'cart')
		.order_by('-id')
	)
	cart_items = []
	total_amount = Decimal('0.00')
	cart_count = 0
	for item in cart_queryset:
		line_total = item.price * item.quantity
		cart_items.append({'item': item, 'line_total': line_total})
		total_amount += line_total
		cart_count += item.quantity

	delivery_fee = Decimal('5.00') if cart_items else Decimal('0.00')
	service_tax = (total_amount * Decimal('0.05')).quantize(Decimal('0.01'))
	grand_total = total_amount + delivery_fee + service_tax

	if request.method == 'POST' and cart_queryset.exists():
		full_name = request.POST.get('full_name', '').strip()
		address = request.POST.get('address', '').strip()
		payment_method = request.POST.get('payment_method', 'esewa').strip()

		if full_name and address:
			# Map payment method display names to database values
			payment_method_map = {
				'eSewa': 'esewa',
				'Cash on Delivery': 'cod',
			}
			payment_method_value = payment_method_map.get(payment_method, 'esewa')

			order = Order.objects.create(
				user=request.user,
				total_amount=grand_total,
				status='pending',
				payment_status='unpaid',
				payment_method=payment_method_value,
			)

			order_items = [
				OrderItem(
					order=order,
					product=item['item'].product,
					selected_option=item['item'].selected_option,
					price=item['item'].price,
					quantity=item['item'].quantity,
				)
				for item in cart_items
			]
			OrderItem.objects.bulk_create(order_items)

			# If eSewa payment, redirect to payment form
			if payment_method_value == 'esewa':
				return redirect(f'/esewa_form/?o_id={order.id}&c_id={current_cart.id}')

			# If COD, clear cart and redirect to orders
			cart_queryset.delete()
			return redirect('orders')

	context = {
		'cart_items': cart_items,
		'total_amount': total_amount,
		'delivery_fee': delivery_fee,
		'service_tax': service_tax,
		'grand_total': grand_total,
		'cart_count': cart_count,
	}
	return render(request, 'cart/checkout_page.html', context)
