from cart.models import Cart
from django.db.models import Sum


def cart_count(request):
    if not request.user.is_authenticated:
        return {'cart_count': 0}

    current_cart = Cart.objects.filter(user=request.user).order_by('-id').first()
    if not current_cart:
        return {'cart_count': 0}

    count = current_cart.items.aggregate(total=Sum('quantity')).get('total') or 0
    return {'cart_count': int(count)}
