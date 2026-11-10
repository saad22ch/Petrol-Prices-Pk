import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def fetch_pso_prices():
    """Scrapes latest fuel rates directly from PSO official website."""
    url = "https://psopk.com/en/fuels/fuel-prices"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        petrol_price = None
        diesel_price = None

        # Parse text/tables for Petrol Super and HSD rates
        text = soup.get_text()
        petrol_match = re.search(
            r"(?:Petrol|Super)[^\d]*(\d{3}\.\d{2}|\d{3})", text, re.IGNORECASE
        )
        diesel_match = re.search(
            r"(?:Diesel|HSD)[^\d]*(\d{3}\.\d{2}|\d{3})", text, re.IGNORECASE
        )

        if petrol_match:
            petrol_price = float(petrol_match.group(1))
        if diesel_match:
            diesel_price = float(diesel_match.group(1))

        return petrol_price, diesel_price
    except Exception as e:
        print(f"Error scraping PSO site: {e}")
        return None, None


def main():
    petrol, diesel = fetch_pso_prices()

    if not petrol or not diesel:
        print("Could not scrape new rates. Keeping existing prices.json.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Load existing prices.json file
    try:
        with open("prices.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"updated": today_str, "history": []}

    history = data.get("history", [])

    # Check if latest record has different values or needs a new entry
    if history:
        last_entry = history[-1]
        if last_entry.get("petrol") == petrol and last_entry.get(
            "diesel"
        ) == diesel:
            print("No price revision detected. Skipping JSON update.")
            return

    # Append new price revision
    new_entry = {"d": today_str, "petrol": petrol, "diesel": diesel}
    history.append(new_entry)
    data["updated"] = today_str
    data["history"] = history

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(
        f"Updated prices.json with Petrol: Rs. {petrol}, Diesel: Rs. {diesel}"
    )


if __name__ == "__main__":
    main()
