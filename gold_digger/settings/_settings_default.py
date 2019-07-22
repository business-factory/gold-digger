# -*- coding: utf-8 -*-

from ._utils import get_env

DEVELOPMENT_MODE = True

DATABASE_DIALECT = "postgresql"
DATABASE_HOST = get_env("database_host", default="127.0.0.1")
DATABASE_PORT = get_env("database_port", default="5432")
DATABASE_USER = get_env("database_user", default="postgres")
DATABASE_PASSWORD = get_env("database_password", default="postgres")
DATABASE_NAME = get_env("database_name", default="golddigger")

GRAYLOG_ADDRESS = "logs.roihunter.com"
GRAYLOG_PORT = 12211

SUPPORTED_CURRENCIES = {
    "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "ATS", "AUD", "AWG", "AZN", "BAM", "BBD",
    "BDT", "BEF", "BGN", "BHD", "BIF", "BMD", "BND", "BOB", "BRL", "BSD", "BTC", "BTN", "BWP",
    "BYR", "BZD", "CAD", "CDF", "CHF", "CLF", "CLP", "CNH", "CNY", "COP", "CRC", "CUC", "CUP",
    "CVE", "CYP", "CZK", "DEM", "DJF", "DKK", "DOP", "DZD", "EEK", "EGP", "ERN", "ESP", "ETB",
    "EUR", "FIM", "FJD", "FKP", "FRF", "GBP", "GEL", "GGP", "GHS", "GIP", "GMD", "GNF", "GRD",
    "GTQ", "GYD", "HKD", "HNL", "HRK", "HTG", "HUF", "IDR", "IEP", "ILS", "IMP", "INR", "IQD",
    "IRR", "ISK", "ITL", "JEP", "JMD", "JOD", "JPY", "KES", "KGS", "KHR", "KMF", "KPW", "KRW",
    "KWD", "KYD", "KZT", "LAK", "LBP", "LKR", "LRD", "LSL", "LTL", "LUF", "LVL", "LYD", "MAD",
    "MCF", "MDL", "MGA", "MKD", "MMK", "MNT", "MOP", "MRO", "MTL", "MUR", "MVR", "MWK", "MXN",
    "MYR", "MZN", "NAD", "NGN", "NIO", "NLG", "NOK", "NPR", "NZD", "OMR", "PAB", "PEN", "PGK",
    "PHP", "PKR", "PLN", "PTE", "PYG", "QAR", "RON", "RSD", "RUB", "RWF", "SAR", "SBD", "SCR",
    "SDG", "SEK", "SGD", "SHP", "SIT", "SLL", "SML", "SOS", "SRD", "STD", "SYP", "SZL", "THB",
    "TJS", "TMT", "TND", "TOP", "TRY", "TTD", "TWD", "TZS", "UAH", "UGX", "USD", "UYU", "UZS",
    "VAL", "VEB", "VEF", "VND", "VUV", "WST", "XAF", "XAG", "XAU", "XCD", "XCP", "XDR", "XOF",
    "XPD", "XPF", "XPT", "YER", "ZAR", "ZMK", "ZMW", "ZWL"
}

SECRETS_CURRENCY_LAYER_ACCESS_KEY = get_env("secrets_currency_layer_access_key", default="")
SECRETS_FIXER_ACCESS_KEY = get_env("secrets_fixer_access_key", default="")
