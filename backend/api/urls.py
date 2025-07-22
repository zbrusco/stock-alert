from django.urls import path
from .views import PriceDataView as data

urlpatterns = [
    path("get-ticker/<str:symbol>/", data.as_view(), name="get_ticker"),
]
