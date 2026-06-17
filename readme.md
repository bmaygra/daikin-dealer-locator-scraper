# Daikin Dealer Locator Web Scraper

A Python web scraper that collects Daikin HVAC dealer/contractor information 
from the Daikin Comfort dealer locator for a defined geographic region.

## Overview

This tool automates the collection of Daikin dealer data by ZIP code, 
extracting contractor name, contact information, address, and dealer type. 
Results are deduplicated and exported to a CSV file for use in marketing 
and sales analysis.

## Requirements

Install dependencies with:

pip install requests beautifulsoup4 lxml pandas openpyxl

## Input

An Excel file (.xls) containing ZIP codes sourced from the USPS Zip Code lookup,
with the following required columns:

- PHYSICAL STATE — two letter state abbreviation (e.g. WA, OR)
- PHYSICAL ZIP — five digit ZIP code

## Usage

1. Place your ZIP code Excel file in your Downloads folder
2. Update ZIP_FILE and OUT_FILE paths in the configuration section if needed
3. Run the script:

python daikin_scraper_portfolio.py

## Configuration

- **Region** — currently configured for AK, ID, MT, OR, WA. Update allowed_states in load_zip_codes() to change
- **Test Mode** — set test_mode = True in main() to limit scraping to the first 10 ZIP codes
- **Output** — results saved as a CSV to your Downloads folder

## Output Fields

| Field | Description |
|---|---|
| search_zip | ZIP code used for the search |
| name | Dealer business name |
| dealer_type | Type of dealer/contractor |
| email | Contact email address |
| phone | Contact phone number |
| street | Street address |
| city | City |
| state | State |
| zip | Dealer ZIP code |