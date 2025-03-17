import requests
import json
from datetime import datetime
import time
from . import GlobalParameters

class CurrencyExchange:
    def __init__(self, base_currency="EUR"):
        self.base_currency = base_currency
        self.api_url = f"https://open.er-api.com/v6/latest/{base_currency}"
        self.rates = {}
        self.last_update = None

    def fetch_rates(self):
        """Fetch the latest exchange rates"""
        try:
            response = requests.get(self.api_url)
            data = response.json()

            if response.status_code == 200 and data["result"] == "success":
                self.rates = data["rates"]
                self.last_update = datetime.fromtimestamp(data["time_last_update_unix"])
                return True
            else:

                return False

        except requests.exceptions.RequestException as e:

            return False
        except (KeyError, json.JSONDecodeError) as e:

            return False

    def get_rate(self, target_currency):
        """Get the exchange rate for a specific currency"""
        if not self.rates or target_currency not in self.rates:
            if not self.fetch_rates():
                return None

        return self.rates.get(target_currency)

    def convert(self, amount, target_currency):
        """Convert an amount from base currency to target currency"""
        rate = self.get_rate(target_currency)
        if rate is None:
            return None

        return amount * rate

    def monitor_rate(self, target_currency, interval=60, duration=300):
        """Monitor the exchange rate for a specific period"""
        end_time = time.time() + duration

        while time.time() < end_time:
            rate = self.get_rate(target_currency)
            if rate:
                print(f"{self.base_currency} to {target_currency} Rate: {rate} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("Failed to fetch rate")

            time.sleep(interval)

if __name__ == "__main__":
    # Create an exchange rate object with EUR as base currency
    exchange = CurrencyExchange("EUR")

    # Get current EUR to RUB rate
    rub_rate = exchange.get_rate("RUB")
    if rub_rate:
        print(f"Current EUR to RUB Rate: {rub_rate}")
        print(f"Last Updated: {exchange.last_update}")

        # Example conversion
        amount = 100
        converted = exchange.convert(amount, "RUB")
        print(f"{amount} EUR = {converted} RUB")
