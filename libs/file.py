import requests
import time
import json
from datetime import datetime, timedelta
from pprint import pprint

# Your slack webhooks
slack_webhook = 'https://hooks.slack.com/services/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'

# List of API keys and their names
api_keys = {'team3': 'px7APGjSxq84Hh0QerVLg', 'posthaste': '3MfKibGgStWkRwPyO2oOVA'}

# Last seen conversion id
last_conversion_id = ''

for account_name, api_key in api_keys.items():
    while True:
        # Get today and tomorrow's date
        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        # Make the POST request to the API
        response = requests.post(
            'https://api.eflow.team/v1/affiliates/reporting/conversions?page=1&page_size=100&order_field=conversion_unix_timestamp&order_direction=desc',
            headers={
                'Content-Type': 'application/json',
                'x-eflow-api-key': api_key
            },
            data=json.dumps({
                "timezone_id": 80,
                "from": today.strftime('%Y-%m-%d'),
                "to": tomorrow.strftime('%Y-%m-%d'),
                "show_events": True,
                "show_conversions": True,
                "query": {
                    "filters": [],
                    "search_terms": []
                }
            })
        )

        # Get the data from the response
        data = response.json()

        # Check if a new sale has been made
        if data['conversions'][0]['conversion_id'] != last_conversion_id:
            # Update the last conversion id
            last_conversion_id = data['conversions'][0]['conversion_id']

            # Format conversion details
            sale = data['conversions'][0]
            details = {
                'Account Name': account_name,
                'Offer': "["+str(sale['relationship']['offer']['network_offer_id'])+"] "+sale['relationship']['offer']['name'],
                'Revenue': sale['revenue'],
                'Device Type': sale['device_type'],
                'Revenue Type': sale['revenue_type'],
                'Conversion Timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(sale['conversion_unix_timestamp'])),
                'Conversion ID': sale['conversion_id'],
            }

            # Prepare slack message
            message = "New Sale Alert 🚀\n"
            message += "\n".join(f"*{k}*: {v}" for k, v in details.items())

            # Send a message to the slack channel
            slack_message = {'text': message}
            requests.post(
                slack_webhook,
                data=json.dumps(slack_message),
                headers={'Content-Type': 'application/json'}
            )
        
        # Sleep for 1 minute (adjust this to control the frequency of checking the API)
        time.sleep(60)
