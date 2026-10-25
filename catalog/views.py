from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

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
