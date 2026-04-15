from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Order


@login_required
def order_page_view(request):
	orders = (
		Order.objects.filter(user=request.user)
		.prefetch_related('items__product')
		.order_by('-created_at')
	)
	latest_order = orders.first()
	total_orders = orders.count()
	lifetime_spent = sum((order.total_amount for order in orders), start=0)
	completed_orders = orders.filter(status='completed').count()
	loyalty_points = total_orders * 75

	order_preview = []
	if latest_order:
		for item in latest_order.items.select_related('product').all():
			order_preview.append({
				'item': item,
				'line_total': item.price * item.quantity,
			})

	context = {
		'orders': orders,
		'latest_order': latest_order,
		'order_preview': order_preview,
		'total_orders': total_orders,
		'lifetime_spent': lifetime_spent,
		'completed_orders': completed_orders,
		'loyalty_points': loyalty_points,
	}
	return render(request, 'orders/order_page.html', context)
