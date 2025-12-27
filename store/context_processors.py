from .models import Cart


def cart_context(request):
    if request.session.session_key:
        cart_items = Cart.objects.filter(session_key=request.session.session_key)
        cart_count = sum(item.quantity for item in cart_items)
        cart_total = sum(item.total_price for item in cart_items)
    else:
        cart_count = 0
        cart_total = 0

    return {
        'cart_count': cart_count,
        'cart_total': cart_total,
    }