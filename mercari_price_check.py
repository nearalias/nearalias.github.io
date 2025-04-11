import requests
import os
from playwright.sync_api import sync_playwright
from datetime import datetime, timezone

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
MANBU_USER_ID = os.getenv("MANBU_USER_ID")

LISTINGS = [
    {
        "name": "Dark Magician of Chaos",
        "code": "IOC-AE065",
        "condition": "ARS 10+",
        "threshold": 4222222,
        "url": "https://jp.mercari.com/item/m20120586668",
    },
    {
        "name": "The Legendary Exodia Incarnate",
        "code": "INFO-AE121",
        "condition": "Raw",
        "threshold": 444000,
        "url": "https://jp.mercari.com/item/m50786306316",
    },
    {
        "name": "Dark Paladin AE",
        "code": "MFC-105",
        "condition": "ARS 10",
        "threshold": 57000,
        "url": "https://jp.mercari.com/item/m55582292120",
    },
    {
        "name": "Yata-Garasu AE",
        "code": "LOD-000",
        "condition": "ARS 10",
        "threshold": 72222,
        "url": "https://jp.mercari.com/item/m89064529226",
    },
    {
        "name": "Black Luster Soldier - Envoy of the Beginning",
        "code": "IOC-AE025",
        "condition": "ARS 10",
        "threshold": 222222,
        "url": "https://jp.mercari.com/item/m51195221403",
    },
    {
        "name": "Chaos Emperor Dragon - Envoy of the End",
        "code": "IOC-AE000",
        "condition": "PSA 10",
        "threshold": 144444,
        "url": "https://jp.mercari.com/item/m12171828346",
    },
    {
        "name": "Stardust Dragon",
        "code": "YCSC",
        "condition": "PSA 10",
        "threshold": 288888,
        "url": "https://jp.mercari.com/item/m85237536985",
    },
    {
        "name": "Injection Fairy Lily",
        "code": "24CC-AE001",
        "condition": "PSA 10",
        "threshold": 72222,
        "url": "https://jp.mercari.com/item/m26357508234",
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
        name = f"{item['name']} - ({item['code']}) - {item['condition']}\u200b"
        value = f"Current Price: **¥{item['price']:,}** (Threshold: ¥{item['threshold']:,}) [View  ]({item['url']})\u200b"

        fields.append(
            {
                "name": name,
                "value": value,
                "inline": False,
            }
        )

    payload = {
        "embeds": [
            {
                "title": "📉 Mercari Price Check",
                "description": f"<@{MANBU_USER_ID}> The following items have dropped below thresholds:",
                "color": 0x7FFFD4,
                "fields": fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                # "footer": {"text": "Mercari Price Tracker"},
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
