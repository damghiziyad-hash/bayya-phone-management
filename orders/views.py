from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Prefetch
from django.shortcuts import redirect
from django.views.generic import ListView

from accounts.models import Role
from .services import confirm_order
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views import View

from catalog.models import Product
from core.models import Status

from .forms import CheckoutForm
from .models import Customer, Order, OrderItem


class CheckoutView(View):
    template_name = "orders/checkout.html"

    def get_product(self, product_id, *, lock=False):
        if not product_id or not str(product_id).isdigit():
            raise Http404("Produit introuvable.")

        queryset = Product.objects.filter(status=Status.ACTIVE)

        if lock:
            queryset = queryset.select_for_update()

        return get_object_or_404(queryset, pk=product_id)

    def get(self, request):
        product = self.get_product(request.GET.get("product_id"))

        form = CheckoutForm(initial={
            "quantity": request.GET.get("quantity", 1),
        })

        return render(request, self.template_name, {
            "form": form,
            "product": product,
        })

    def post(self, request):
        form = CheckoutForm(request.POST)
        product_id = request.POST.get("product_id")

        if not form.is_valid():
            product = self.get_product(product_id)
            return render(request, self.template_name, {
                "form": form,
                "product": product,
            })

        with transaction.atomic():
            product = self.get_product(product_id, lock=True)
            quantity = form.cleaned_data["quantity"]

            if quantity > product.quantity:
                form.add_error(
                    "quantity",
                    "La quantité demandée dépasse le stock disponible.",
                )
                return render(request, self.template_name, {
                    "form": form,
                    "product": product,
                })

            customer = Customer.objects.create(
                full_name=form.cleaned_data["full_name"],
                phone=form.cleaned_data["phone"],
                city=form.cleaned_data["city"],
                address=form.cleaned_data["address"],
                email=form.cleaned_data["email"],
            )

            order = Order.objects.create(customer=customer)

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.display_name,
                unit_price=product.sale_price,
                quantity=quantity,
            )

        return render(request, "orders/checkout_success.html", {
            "order": order,
        })
class OrderListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    permission_required = "catalog.view_product"

    def get_queryset(self):
        return (
            Order.objects.select_related("customer")
            .prefetch_related("items")
            .order_by("-created_at")
        )


class OrderConfirmView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "catalog.view_product"

    def post(self, request, pk):
        if request.user.role not in (Role.OWNER, Role.STOCK_MANAGER):
            raise PermissionDenied

        try:
            order = confirm_order(order_id=pk, user=request.user)
        except (ValidationError,):
            messages.error(
                request,
                "Impossible de confirmer la commande. Vérifiez son statut et le stock.",
            )
        except Exception as exc:
            # Ne pas exposer les détails techniques à l'utilisateur.
            from inventory.services import StockError
            from django.core.exceptions import PermissionDenied as StockPermissionDenied

            if isinstance(exc, (StockError, StockPermissionDenied)):
                messages.error(request, str(exc))
            else:
                raise
        else:
            messages.success(
                request,
                f"La commande #{order.pk} a été confirmée.",
            )

        return redirect("orders:order_list")
