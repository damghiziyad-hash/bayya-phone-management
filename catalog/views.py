from django.db import transaction
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.views.generic import DetailView
from core.models import Status
from .forms import ProductForm
from .models import Category, Product


class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "catalog.view_product"
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        queryset = Product.objects.select_related("category").all()

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(sku__icontains=query)
                | Q(barcode__icontains=query)
                | Q(name_fr__icontains=query)
                | Q(name_ar__icontains=query)
                | Q(phone_brand__icontains=query)
                | Q(phone_model__icontains=query)
            )

        category_id = self.request.GET.get("category", "")
        if category_id.isdigit():
            queryset = queryset.filter(category_id=int(category_id))

        status = self.request.GET.get("status", "")
        if status in ("active", "archived"):
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.order_by("name_fr")
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["can_add_product"] = self.request.user.has_perm("catalog.add_product")
        context["can_delete_product"] = self.request.user.has_perm( "catalog.delete_product")
        context["can_change_product"] = self.request.user.has_perm("catalog.change_product")
        context["can_view_purchase_price"] = self.request.user.has_perm(
            "catalog.view_purchase_price"
        )
        return context


class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "catalog.add_product"
    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "catalog.change_product"
    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    template_name = "catalog/product_confirm_delete.html"
    permission_required = "catalog.delete_product"
    success_url = reverse_lazy("catalog:product_list")

    def form_valid(self, form):
        product = self.object

        # Refuser la suppression si le produit a un historique
        if product.movements.exists() or product.order_items.exists():
            messages.error(
                self.request,
                "Ce produit possède un historique de stock ou des commandes. "
                "Archivez-le au lieu de le supprimer."
            )
            return redirect("catalog:product_list")

        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Suppression impossible : ce produit est utilisé par d'autres données."
            )
            return redirect("catalog:product_list")


class ProductArchiveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "catalog.change_product"

    @transaction.atomic
    def post(self, request, pk):
        # نفس القفل المستعمل في inventory.services.record_movement
        product = get_object_or_404(
            Product.objects.select_for_update(),
            pk=pk,
        )

        if product.status == Status.ARCHIVED:
            messages.info(request, "Ce produit est déjà archivé.")
            return redirect("catalog:product_list")

        if product.quantity > 0:
            messages.error(
                request,
                "Impossible d'archiver ce produit : il reste du stock. "
                "Enregistrez d'abord une sortie de stock."
            )
            return redirect("catalog:product_list")

        product.status = Status.ARCHIVED
        product.save(update_fields=["status", "updated_at"])

        messages.success(
            request,
            f"Le produit « {product.display_name} » a été archivé."
        )
        return redirect("catalog:product_list")

class ClientProductListView(ListView):
    """Catalogue public des produits actifs."""

    template_name = "catalog/client_product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.select_related("category").filter(
            status=Status.ACTIVE
        )

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name_fr__icontains=query)
                | Q(name_ar__icontains=query)
                | Q(phone_brand__icontains=query)
                | Q(phone_model__icontains=query)
                | Q(category__name_fr__icontains=query)
                | Q(category__name_ar__icontains=query)
            )

        return queryset


class ClientProductDetailView(DetailView):
    """Détails publics d'un produit actif."""

    model = Product
    template_name = "catalog/client_product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.select_related("category").filter(
            status=Status.ACTIVE
        )

