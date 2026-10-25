from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView
from .models import StockMovement
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views import View

from .forms import StockInForm
from .models import MovementType
from .services import StockError, record_movement


class StockInView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "inventory.add_stockmovement"
    raise_exception = True
    template_name = "inventory/stock_in.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": StockInForm()},
        )

    def post(self, request):
        form = StockInForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            supplier = data["supplier"].strip()
            note = data["note"].strip()

            reason_parts = []
            if supplier:
                reason_parts.append(f"Fournisseur: {supplier}")
            if note:
                reason_parts.append(note)

            try:
                record_movement(
                    product=data["product"],
                    movement_type=MovementType.IN,
                    quantity=data["quantity"],
                    user=request.user,
                    reason=" | ".join(reason_parts),
                    reference=data["reference"].strip(),
                )
            except StockError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(
                    request,
                    _("Entrée enregistrée : %(quantity)s unité(s) pour %(product)s.")
                    % {
                        "quantity": data["quantity"],
                        "product": data["product"].display_name,
                    },
                )
                return redirect("inventory:stock_in")

        return render(request, self.template_name, {"form": form})
class StockMovementListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StockMovement
    template_name = "inventory/stock_movement_list.html"
    context_object_name = "movements"
    permission_required = "inventory.view_stockmovement"
    raise_exception = True
    paginate_by = 20

    def get_queryset(self):
        queryset = StockMovement.objects.select_related(
            "product", "created_by"
        ).all()

        movement_type = self.request.GET.get("type", "").strip()
        search = self.request.GET.get("q", "").strip()

        valid_types = {choice[0] for choice in MovementType.choices}
        if movement_type in valid_types:
            queryset = queryset.filter(movement_type=movement_type)

        if search:
            queryset = queryset.filter(
                Q(product__sku__icontains=search)
                | Q(product__name_fr__icontains=search)
                | Q(product__name_ar__icontains=search)
                | Q(reference__icontains=search)
                | Q(reason__icontains=search)
                | Q(created_by__username__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["movement_types"] = MovementType.choices
        context["selected_type"] = self.request.GET.get("type", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context
