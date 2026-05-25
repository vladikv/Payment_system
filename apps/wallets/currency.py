import requests
from django.conf import settings
from django.core.cache import cache


def get_exchange_rates(base_currency: str = 'USD') -> dict:
    """
    Get exchange rates for a base currency.
    Caches results for 1 hour to avoid excessive API calls.
    """
    cache_key = f'exchange_rates_{base_currency}'
    cached = cache.get(cache_key)

    if cached:
        return cached

    try:
        api_key = settings.EXCHANGE_RATE_API_KEY
        url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}'
        response = requests.get(url, timeout=5)
        data = response.json()

        if data['result'] == 'success':
            rates = data['conversion_rates']
            cache.set(cache_key, rates, timeout=3600)  # cache for 1 hour
            return rates

    except Exception:
        pass

    # Fallback rates if API fails
    return {'USD': 1.0, 'EUR': 0.92, 'UAH': 41.0}


def convert_amount(amount, from_currency: str, to_currency: str) -> float:
    """Convert amount from one currency to another."""
    if from_currency == to_currency:
        return float(amount)

    rates = get_exchange_rates(from_currency)
    rate = rates.get(to_currency)

    if not rate:
        return float(amount)

    return round(float(amount) * rate, 2)