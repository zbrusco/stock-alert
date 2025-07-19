from django.db import models


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    exchange = models.CharField(max_length=20)


class StockMetadata(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    asset_type = models.CharField(max_length=50)
    sector = models.CharField(max_length=50)
    market_cap = models.BigIntegerField()
    last_updated = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["stock", "last_updated"]),
            models.Index(fields=["sector", "market_cap"]),
            models.Index(fields=["asset_type"]),
            models.Index(fields=["sector", "asset_type", "market_cap"]),
        ]


class UnobtainableRange(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    timeframe = models.CharField(max_length=10)
    start = models.DateTimeField()
    end = models.DateTimeField()
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["stock", "timeframe", "start", "end"]
        indexes = [
            models.Index(fields=["stock", "timeframe", "start", "end"]),
        ]


class BasePrice(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.BigIntegerField()

    class Meta:
        abstract = True
        unique_together = ("stock", "timestamp")
        indexes = [
            models.Index(fields=["stock", "timestamp"]),
        ]


# Add more timeframe models if needed
class StockPrice5Min(BasePrice):
    pass


class StockPrice15Min(BasePrice):
    pass


class StockPrice1H(BasePrice):
    pass


class StockPrice1D(BasePrice):
    pass


class StockPrice1Month(BasePrice):
    pass
