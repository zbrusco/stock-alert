from rest_framework import serializers
from market_data.models import BasePrice


class StockPriceSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    volume = serializers.IntegerField()

    class Meta:
        fields = ["timestamp", "open", "high", "low", "close", "volume"]
