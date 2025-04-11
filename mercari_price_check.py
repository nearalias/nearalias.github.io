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
        "threshold": 222222,
        "url": "https://jp.mercari.com/item/m20120586668",
        "user_ids": [MANBU_USER_ID],
    },
    {
        "name": "The Legendary Exodia Incarnate",
        "code": "INFO-AE121",
        "condition": "Raw",
        "threshold": 44000,
        "url": "https://jp.mercari.com/item/m50786306316",
        "user_ids": [MANBU_USER_ID],
    },
    {
        "name": "Dark Paladin AE",
        "code": "MFC-105",
        "condition": "ARS 10",
        "threshold": 57000,
        "url": "https://jp.mercari.com/item/m55582292120",
        "user_ids": [MANBU_USER_ID],
    },
    {
        "name": "Yata-Garasu AE",
        "code": "LOD-000",
        "condition": "ARS 10",
        "threshold": 72222,
        "url": "https://jp.mercari.com/item/m89064529226",
        "user_ids": [MANBU_USER_ID],
    },
    {
        "name": "Black Luster Soldier - Envoy of the Beginning",
        "code": "IOC-AE025",
        "condition": "ARS 10",
        "threshold": 222222,
        "url": "https://jp.mercari.com/item/m51195221403",
        "user_ids": [MANBU_USER_ID],
    },
    {
        "name": "Chaos Emperor Dragon - Envoy of the End",
        "code": "IOC-AE000",
        "condition": "PSA 10",
        "threshold": 9144444,
        "url": "https://jp.mercari.com/item/m12171828346",
        "user_ids": [MANBU_USER_ID, "1000000000000000000"],
    },
    {
        "name": "Stardust Dragon",
        "code": "YCSC",
        "condition": "PSA 10",
        "threshold": 288888,
        "url": "https://jp.mercari.com/item/m85237536985",
        "user_ids": [MANBU_USER_ID],
    },
    {
        "name": "Injection Fairy Lily",
        "code": "24CC-AE001",
        "condition": "PSA 10",
        "threshold": 72222,
        "url": "https://jp.mercari.com/item/m26357508234",
        "user_ids": [MANBU_USER_ID],
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
    user_ids_to_notify = []
    description_lines = []
    for item in items:
        user_ids_to_notify.extend(item["user_ids"])
        description_lines.append(
            f"• **{item['name']} - {item['code']} - {item['condition']}**\n"
            f"  Price: **¥{item['price']:,}** (Threshold: ¥{item['threshold']:,}) - [Link]({item['url']})"
        )

    user_ids_to_notify = list(set(user_ids_to_notify))
    user_ids = ", ".join([f"<@{user_id}>" for user_id in user_ids_to_notify])

    payload = {
        "embeds": [
            {
                "title": "📉 Mercari Price Check",
                "description": f"{user_ids} The following items have dropped below thresholds:\n\n" + "\n\n".join(description_lines),
                "color": 0x7FFFD4,
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
