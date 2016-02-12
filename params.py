
DEFAULT_CONFIG_PARAMS = {
    "base_currency": "USD",
    "origin_date": "2015-01-01",
    "database": {
        "user": "gold-digger",
        "pass": "digdig",
        "name": "gold-digger",
        "host": "127.0.0.1",
        "port": "5433",
        "dialect": "postgres"
    },
    "data_providers": {
        "currency_layer": "http://www.apilayer.net/api/live?access_key=8497c277171dfc3ad271f1ccb733a6a8",
        "grandtrunk": "http://currencies.apps.grandtrunk.net/"
    }
}
