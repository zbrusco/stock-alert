import os


def get_api_credentials():
    return {
        "alpaca_key": os.environ.get("api_key_alpaca"),
        "alpaca_secret": os.environ.get("api_secret_alpaca"),
        "finage_key": os.environ.get("api_key_finage"),
        "polygon_key": os.environ.get("api_key_polygon"),
        "tiingo_key": os.environ.get("api_key_tiingo"),
    }
