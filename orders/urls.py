
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("commander/", views.CheckoutView.as_view(), name="checkout"),
    path("gestion/", views.OrderListView.as_view(), name="order_list"),
    path(
        "gestion/<int:pk>/confirmer/",
        views.OrderConfirmView.as_view(),
        name="order_confirm",
    ),
]
