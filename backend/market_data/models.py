from django.db import models


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)


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
