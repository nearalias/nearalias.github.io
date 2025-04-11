import requests
import os
from playwright.sync_api import sync_playwright
from datetime import datetime, timezone

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

LISTINGS = [
    {
        "name": "Dark Magician of Chaos",
        "code": "IOC-AE065",
        "condition": "ARS 10+",
        "threshold": 215000,
        "url": "https://jp.mercari.com/item/m20120586668",
    },
    {
        "name": "The Legendary Exodia Incarnate",
        "code": "INFO-AE121",
        "condition": "Raw",
        "threshold": 43000,
        "url": "https://jp.mercari.com/item/m50786306316",
    },
]


def fetch_price(listing_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless: True to run without GUI
        page = browser.new_page()
        page.goto(listing_url)

        # Wait for the price element to be visible (adjust selector based on the actual page structure)
        page.wait_for_selector('[data-testid="price"]')

        # Get the price text from the page
        price_element = page.query_selector('[data-testid="price"]')
        
        if price_element:
            # Extract the price part
            price = price_element.query_selector('span:nth-child(2)').inner_text().strip().replace(",", "")
            browser.close()
            
            # Combine and return the price as an integer
            return int(price)
        else:
            browser.close()
            return None


def send_discord_alert(items):
    fields = []
    for item in items:
        fields.append(
            {
                "name": f"{item['name']} - ({item['code']}) - {item['condition']}",
                "value": f"[View Listing]({item['url']})\n💴 **¥{item['price']:,}** (Threshold: ¥{item['threshold']:,})",
                "inline": False,
            }
        )

    payload = {
        "embeds": [
            {
                "title": "📉 Mercari Price Check",
                "description": "The following items have dropped below your desired threshold:",
                "color": 0x00FF00,
                "fields": fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": "Mercari Price Tracker"},
            }
        ]
    }

    res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if res.status_code not in (200, 204):
        print(f"Failed to send Discord message: {res.text}")


def main():
    dropped_items = []

    for listing in LISTINGS:
        try:
            current_price = fetch_price(listing["url"])
            if current_price <= listing["threshold"]:
                dropped_items.append(
                    {
                        "name": listing["name"],
                        "code": listing["code"],
                        "condition": listing["condition"],
                        "url": listing["url"],
                        "price": current_price,
                        "threshold": listing["threshold"],
                    }
                )
        except Exception as e:
            print(f"Error fetching price for {listing['name']}: {e}")

    if dropped_items:
        send_discord_alert(dropped_items)
    else:
        print("No price drops detected.")


if __name__ == "__main__":
    main()
