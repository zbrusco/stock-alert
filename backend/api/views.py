from data_ingestion.services import ensure_data, get_timeframe_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import StockPriceSerializer
import datetime


class PriceDataView(APIView):
    def get(self, request):
        symbol = request.query_params.get("symbol").upper()
        timeframe = request.query_params.get("timeframe")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        limit = request.query_params.get("limit", "100")

        if not all([symbol, timeframe, start, end]):
            return Response(
                {
                    "error": "symbol, timeframe, start date, and end date are required parameters."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Date validation
        try:
            end_date = datetime.datetime.fromisoformat(end)
            start_date = datetime.datetime.fromisoformat(start)
            if start_date > end_date:
                return Response(
                    {"error": "Start date must be before end date."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if end_date > datetime.date.today():
                end_date = datetime.date.today()
        except ValueError:
            return Response({"error": "Invalid date format. (YYYY-MM-DD only)"})

        # Limit validation
        try:
            limit_query = int(limit)
            if limit_query < 1:
                raise Exception(ValueError)
            if limit_query > 200:
                limit_query = 200
        except ValueError:
            return Response(
                {"error": "Invalid limit value. Must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Timeframe validation
        PriceModel = get_timeframe_model(timeframe)

        # Check the DB
        is_data_ready = ensure_data(
            symbol, timeframe, start_date, end_date, limit_query
        )
        if not is_data_ready:
            return Response(
                {
                    "error": "Data could not be found in the database or fetched from external sources."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Query the DB
        query = PriceModel.objects.filter(
            stock__symbol__iexact=symbol,
            timestamp__gte=start_date,
            timestamp__lte=end_date,
        ).order_by("-timestamp")[:limit_query]

        serializer = StockPriceSerializer(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
