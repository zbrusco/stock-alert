from rest_framework import serializers


class StockPriceSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    volume = serializers.IntegerField()

    class Meta:
        fields = ["timestamp", "open", "high", "low", "close", "volume"]
