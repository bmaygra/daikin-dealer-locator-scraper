# Daikin Dealer Locator Webscraper for Marketing

from pathlib import Path
from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
import re


#Configuration

BASE_URL = "https://daikincomfort.com"
SEARCH_URL= f"{BASE_URL}/contractor"

HEADERS = {"User-Agent": "Mozilla/5.0",
           "Accept-Language": "en-US,en;q=0.9"
           }

ZIP_FILE = Path.home() / "Downloads" / "Zip_Locale_Detail.xls"
OUT_FILE = Path.home() / "Downloads" / "Output_File.csv"



def clean(s:str) -> str:
    """Normalize whitespace in a string: collapse internal runs into a single space,
    strip leading/trailing whitespace, and handles None safely"""
    return re.sub(r"\s+", " ", (s or "")).strip()

def split_city_state_zip(address: str):
    """Extract city, state, and zip code from formatted address string.  Returns a tuple of
    (city, state, zip) or empty strings if there is no match"""
    #Regex matches: "City Name, State, Zip" or "City Name, State, Zip+4
    m = re.search(r"([A-Za-z .'-]+),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)", address)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return "", "", ""

def fetch_html(zip_code: str) -> str:
    """Request dealer locator page for a given zip code and return the raw HTML."""
    r = requests.get(SEARCH_URL, params={"zipCode": zip_code}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def street_address_only(s: str) -> str:
    """Extract street address returning everything before the first comma.  Returns the original
    string if no comma is present"""
    return s.split(",", 1)[0].strip() if "," in s else s


def parse_contractors(html: str, zip_code: str) -> list[dict]:
    """Parse raw HTML from dealer locator page and extract contractor details.  Returns a list of
     dictionaries containing dealer name, phone number, email, unique ID, dealer type, and address fields
     for a given zip code"""
    soup = BeautifulSoup(html, "lxml")
    dealers = soup.select("div.dealerList__each")
    rows = []

    for d in dealers:

        # Get Dealer Name from Title Block
        name_nodes = d.select_one(".dealerList__titleBlock h3")
        name = name_nodes.get_text(" ") if name_nodes else ""

        # Get Phone Number from Telephone Link
        phone = ""
        tel = d.select_one("a[href^='tel:']")
        if tel and tel.get("href"):
            phone = tel["href"].replace("tel:", "").strip()

        #Contractor Email, Unique ID, and Dealer Type
        email = d.get("cntr-email", "") or ""
        unique_id = d.get("uniqueId", "") or d.get("uniqueid") or ""
        dealer_type = d.get("data-type", "") or ""

        # Address Parse
        street = ""
        city = ""
        state = ""
        zip_out = ""

        address_block = d.select_one(".addressBlock")
        if address_block:
            address_lines = [clean(p.get_text(" ")) for p in address_block.find_all("p")]
            address_lines = [ln for ln in address_lines if ln]

            if len(address_lines) >= 1:
                street = street_address_only(address_lines[0])
            if len(address_lines) >= 2:
                city, state, zip_out = split_city_state_zip(address_lines[1])
            else:
                city, state, zip_out = split_city_state_zip(address_block.get_text(" "))


        rows.append({
            "search_zip": zip_code,
                "name": clean(name),
                "dealer_type": clean(dealer_type),
                "unique_id": clean(unique_id),
                "email": clean(email),
                "phone": clean(phone),
                "street": clean(street),
                "city": clean(city),
                "state": clean(state),
                "zip": clean(zip_out),
        })

    print(f"Parsed {len(rows)} dealers for {zip_code}")

    return rows

def load_zip_codes(xls_path: str) -> list[str]:
    """Load and filter ZIP codes from an Excel file for the 5-state region.
    Cleans ZIP codes to handle Excel formatting issues such as trailing decimals and missing leading zeros.
    Raises ValueError if required columns are missing"""
    df = pd.read_excel(xls_path, dtype=str)

    allowed_states = {"AK", "ID", "MT", "OR", "WA"}
    state_col = "PHYSICAL STATE"
    zip_col = "PHYSICAL ZIP"

    if state_col not in df.columns or zip_col not in df.columns:
        raise ValueError(f"Required columns {state_col} and {zip_col} not found in {xls_path}")

    df = df[df[state_col].str.strip().isin(allowed_states)]

    zips = (
        df[zip_col]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(5)
        .dropna()
        .unique()
        .tolist()
    )

    zips.sort()

    print(f"Loaded {len(zips)} ZIP codes from 5-state region")
    return zips

def main():
    """Main function. Loads ZIP codes, scrapes dealer locator for each, deduplicates results by unique
    dealer ID, and saves the final output to CSV.  Test mode included to limit scraping to the first 10
    ZIP codes"""
    if not Path(ZIP_FILE).exists():
        raise FileNotFoundError(f"Zip File not found: {ZIP_FILE}")

    zip_codes = load_zip_codes(ZIP_FILE)
    print(f"Total Zip Codes to Scrape: {len(zip_codes)}")

    all_rows = []

    # Test Mode
    test_mode = False
    zips_to_run = zip_codes[:10] if test_mode else zip_codes

    for i, z in enumerate(zips_to_run, start=1):
        print(f"[{i}/{len(zips_to_run)}] Scraping Zip Code: {z}...")
        try:
            html = fetch_html(z)
            rows = parse_contractors(html, z)
            all_rows.extend(rows)
        except Exception as e:
            print(f"Error on Zip Code {z}: {e}")

        time.sleep(1)

    # Build dataframe once at the end
    df = pd.DataFrame(all_rows)

    # Deduplicate once at the end
    if not df.empty and "unique_id" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["unique_id"], keep="first").reset_index(drop=True)
        print(f"Deduped: {before} -> {len(df)} rows")

    if "unique_id" in df.columns:
        df = df.drop(columns=["unique_id"])

    df.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(df)} rows to {OUT_FILE}")


if __name__ == "__main__":
    main()