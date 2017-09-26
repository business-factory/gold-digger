# -*- coding: utf-8 -*-


DEFAULT_CONFIG_PARAMS = {
    "development_mode": True,
    "database": {
        "user": "postgres",
        "pass": "postgres",
        "name": "gold-digger",
        "host": "127.0.0.1",
        "port": "5432",
        "dialect": "postgres"
    },
    "graylog": {
        "address": "logs.roihunter.com",
        "port": 12211,
    },
    "supported_currencies": {
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
    },
    "secrets": {
        "currency_layer": []
    },
}
