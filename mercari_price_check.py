import json
import os
import requests
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def load_listings():
    with open("listings.json", "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_price_from_mercari(listing_url):
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
            price = (
                price_element.query_selector("span:nth-child(2)")
                .inner_text()
                .strip()
                .replace(",", "")
            )
            browser.close()

            # Combine and return the price as an integer
            return int(price)
        else:
            browser.close()
            return None


def fetch_price(listing_url, website):
    match website:
        case "MERCARI":
            return fetch_price_from_mercari(listing_url)
        case _:
            raise ValueError(f"Unsupported website: {website}")


def send_discord_alert(items):
    users_to_notify = []
    description_lines = []
    for item in items:
        info = item["info"]
        price = item["price"]
        users_to_notify.extend(info["user_ids"])
        description_lines.append(
            f"• **{info['name']} - ({info['code']}) - {info['condition']}**\n"
            f"  Price: **¥{price:,}** (Threshold: ¥{info['threshold']:,}) - [Link]({info['url']})"
        )

    users = ", ".join(f"<@{user_id}>" for user_id in sorted(set(users_to_notify)))

    payload = {
        "content": f"\n\nListing prices have dropped below thresholds! {users}",
        "embeds": [
            {
                # "title": "Price Check Alert",
                "description": "\n\n".join(description_lines),
                "color": 0x7FFFD4,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                # "footer": {"text": "Price Tracker"},
            }
        ]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code not in (200, 204):
        print(f"Failed to send Discord message: {response.text}")


def main():
    listings = load_listings()
    dropped_items = []

    for listing in listings:
        try:
            current_price = fetch_price(listing["url"], listing["website"])
            if current_price <= listing["threshold"]:
                dropped_items.append({"info": listing, "price": current_price})
        except Exception as e:
            print(f"Error fetching price for {listing['name']}: {e}")

    if dropped_items:
        send_discord_alert(dropped_items)
    else:
        print("No price drops detected.")


if __name__ == "__main__":
    main()
