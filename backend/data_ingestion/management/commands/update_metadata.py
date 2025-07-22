from django.core.management.base import BaseCommand
from data_ingestion.metadata.services import ensure_metadata
from market_data.models import Stock


class Command(BaseCommand):
    help = "Update metadata for all stocks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true", help="Force update all metadata"
        )

    def handle(self, *args, **options):
        force = options["force"]
        stocks = Stock.objects.all()
        for stock in stocks:
            symbol = stock.symbol
            success = ensure_metadata(symbol, force_update=force)
            if success:
                self.stdout.write(self.style.SUCCESS(f"Updated metadata: {symbol}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to update: {symbol}"))

    # TODO
    # Implement bulk updates
    # create cronjob to run this script
