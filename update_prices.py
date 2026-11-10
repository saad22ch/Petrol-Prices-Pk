"""Reads PSO's fuel price page and updates prices.json. Python standard library only."""
import html as htmllib, json, re, sys, urllib.request
from datetime import datetime, timedelta

URL = "https://psopk.com/en/fuels/fuel-prices"
FILE = "prices.json"
PATTERN = re.compile(
    r"Effective From:\s*([A-Za-z]+\.? \d{1,2}, \d{4}).{0,200}?"
    r"PREMIER EURO 5\s*Rs\.?\s*([\d,]+(?:\.\d+)?)\s*/\s*Ltr.{0,120}?"
    r"HI-CETANE DIESEL EURO 5\s*Rs\.?\s*([\d,]+(?:\.\d+)?)\s*/\s*Ltr",
    re.I | re.S)


def parse(page):
    text = htmllib.unescape(re.sub(r"<[^>]+>", " ", page))
    text = re.sub(r"\s+", " ", text)
    m = PATTERN.search(text)
    if not m:
        raise ValueError("Could not find the Premier/Hi-Cetane price table. The PSO page layout may have changed.")
    raw = m.group(1).replace(".", "")
    when = None
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            when = datetime.strptime(raw, fmt)
            break
        except ValueError:
            pass
    if when is None:
        raise ValueError("Unrecognised date: " + m.group(1))
    petrol = float(m.group(2).replace(",", ""))
    diesel = float(m.group(3).replace(",", ""))
    if not (100 <= petrol <= 1000 and 100 <= diesel <= 1000):
        raise ValueError("Prices look wrong: petrol %s, diesel %s" % (petrol, diesel))
    if when > datetime.utcnow() + timedelta(days=2):
        raise ValueError("Effective date is in the future: " + when.strftime("%Y-%m-%d"))
    return when.strftime("%Y-%m-%d"), petrol, diesel


def merge(data, d, petrol, diesel):
    hist = data["history"]
    row = {"d": d, "petrol": petrol, "diesel": diesel}
    for i, h in enumerate(hist):
        if h["d"] == d:
            if h["petrol"] == petrol and h["diesel"] == diesel:
                return False
            hist[i] = row
            break
    else:
        if hist and d < hist[-1]["d"]:
            return False  # page shows an older price than we already have
        hist.append(row)
    hist.sort(key=lambda h: h["d"])
    data["history"] = hist[-120:]
    data["updated"] = data["history"][-1]["d"]
    return True


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; PetrolPricePK/1.0)"})
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    d, petrol, diesel = parse(page)
    with open(FILE, encoding="utf-8") as f:
        data = json.load(f)
    if merge(data, d, petrol, diesel):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print("Updated:", d, petrol, diesel)
    else:
        print("No change:", d, petrol, diesel)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
