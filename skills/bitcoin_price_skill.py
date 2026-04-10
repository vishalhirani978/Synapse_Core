# FILENAME: bitcoin_price_skill.py
# PLAN:
# Goal: Fetch the live Bitcoin price in USD from the CoinGecko API and return the numeric price.
# Logic Steps:
#   1. Import the required libraries (requests, json).
#   2. Send a GET request to the CoinGecko API to fetch the Bitcoin price in USD.
#   3. Handle potential exceptions during the API request or JSON parsing.
#   4. Check if the 'bitcoin' and 'usd' keys exist in the response data before accessing them.
#   5. Validate if the bitcoin_price is numeric before returning it.
# Required Libraries: requests, json

class BaseSkill:
    def execute(self, **kwargs):
        pass

class GeneratedSkill(BaseSkill):
    def execute(self, **kwargs):
        try:
            import requests
            import json
            url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            if 'bitcoin' in data and 'usd' in data['bitcoin']:
                bitcoin_price = data['bitcoin']['usd']
                if isinstance(bitcoin_price, (int, float)):
                    return bitcoin_price
                else:
                    return None
            else:
                return None
        except requests.exceptions.RequestException as e:
            # Handle any exceptions during the API request
            return None
        except json.JSONDecodeError as e:
            # Handle any exceptions during JSON parsing
            return None
        except Exception as e:
            # Handle any other exceptions
            return None
