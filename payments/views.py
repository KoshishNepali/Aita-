import base64
import hashlib
import hmac
import json
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from cart.models import Cart
from orders.models import Order
from payments.models import Payment


def _esewa_signature(message, secret_key):
    """Generate eSewa signature as Base64(HMAC_SHA256(message, secret))."""
    digest = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


@login_required
@require_http_methods(["GET"])
def esewa_form(request):
    """Generate form payload for eSewa ePay v2."""
    order_id = request.GET.get("o_id")
    cart_id = request.GET.get("c_id")

    if not order_id or not cart_id:
        messages.error(request, "Invalid order or cart information.")
        return redirect("checkout")

    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart = get_object_or_404(Cart, id=cart_id, user=request.user)

    transaction_uuid = str(uuid.uuid4())
    amount = Decimal(order.total_amount).quantize(Decimal("0.01"))
    tax_amount = Decimal("0.00")
    product_service_charge = Decimal("0.00")
    product_delivery_charge = Decimal("0.00")
    total_amount = amount + tax_amount + product_service_charge + product_delivery_charge

    product_code = settings.ESEWA_MERCHANT_CODE
    signed_field_names = "total_amount,transaction_uuid,product_code"
    signature_message = (
        f"total_amount={total_amount},"
        f"transaction_uuid={transaction_uuid},"
        f"product_code={product_code}"
    )
    signature = _esewa_signature(signature_message, settings.ESEWA_SECRET_KEY)

    Payment.objects.create(
        order=order,
        amount=total_amount,
        transaction_id=transaction_uuid,
        method="eSewa",
        status="pending",
    )

    context = {
        "amount": amount,
        "tax_amount": tax_amount,
        "product_service_charge": product_service_charge,
        "product_delivery_charge": product_delivery_charge,
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
        "product_code": product_code,
        "success_url": request.build_absolute_uri(f"/esewa_verify/{order.id}/{cart.id}/"),
        "failure_url": request.build_absolute_uri("/checkout/"),
        "signed_field_names": signed_field_names,
        "signature": signature,
        "esewa_payment_url": settings.ESEWA_PAYMENT_URL,
    }
    return render(request, "payments/esewaform.html", context)


@login_required
@require_http_methods(["GET"])
def esewa_verify(request, order_id, cart_id):
    """Verify eSewa callback payload and finalize order."""
    encoded_data = request.GET.get("data")
    if not encoded_data:
        messages.error(request, "Payment verification failed.")
        return redirect("checkout")

    try:
        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
        payload = json.loads(decoded_data)
    except Exception:
        messages.error(request, "Invalid payment response received.")
        return redirect("checkout")

    signed_field_names = payload.get("signed_field_names", "")
    received_signature = payload.get("signature", "")

    if not signed_field_names or not received_signature:
        messages.error(request, "Payment signature is missing.")
        return redirect("checkout")

    fields = [field.strip() for field in signed_field_names.split(",") if field.strip()]
    signing_parts = [f"{field}={payload.get(field, '')}" for field in fields]
    signing_message = ",".join(signing_parts)
    expected_signature = _esewa_signature(signing_message, settings.ESEWA_SECRET_KEY)

    if expected_signature != received_signature:
        messages.error(request, "Payment signature verification failed.")
        return redirect("checkout")

    if payload.get("status") != "COMPLETE":
        messages.error(request, "Payment was not completed.")
        return redirect("checkout")

    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart = get_object_or_404(Cart, id=cart_id, user=request.user)

    tx_uuid = payload.get("transaction_uuid", "")
    payment = Payment.objects.filter(order=order, transaction_id=tx_uuid).first()
    if payment:
        payment.status = "completed"
        payment.transaction_id = payload.get("transaction_code", payment.transaction_id)
        payment.save(update_fields=["status", "transaction_id"])

    order.payment_method = "esewa"
    order.payment_status = "paid"
    order.status = "completed"
    order.save(update_fields=["payment_method", "payment_status", "status"])

    cart.delete()
    messages.success(request, "Payment successful! Your order has been confirmed.")
    return redirect("orders")

