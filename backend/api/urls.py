from django.urls import path
from .views import PriceDataView as data

urlpatterns = [
    path("", data.as_view(), name="stock-price-data"),
]
