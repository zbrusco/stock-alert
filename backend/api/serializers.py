from rest_framework import serializers
from market_data.models import BasePrice


class StockPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasePrice
        fields = ["timestamp", "open", "high", "low", "close", "volume"]
