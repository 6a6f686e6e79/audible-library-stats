"""
audible_stats.py
Pulls your full Audible library and listening stats.
Saves raw data to audible_data.json for use with the dashboard.
Run audible_auth.py first if you haven't already.
"""

import audible
import json
import os
from datetime import datetime

AUTH_FILE = 'audible_auth.json'
OUTPUT_FILE = 'audible_data.json'

print("=" * 60)
print("AUDIBLE LIBRARY STATS")
print("=" * 60)

auth = audible.Authenticator.from_file(AUTH_FILE)
client = audible.Client(auth)

output = {}

# ── LIBRARY ───────────────────────────────────────────────────
print("\nFetching library...")
library = client.get(
    'library',
    num_results=1000,
    response_groups='product_attrs,product_desc,listening_status,is_finished,percent_complete,product_details,series,contributors',
    sort_by='-PurchaseDate'
)
output['library'] = library.get('items', [])
print(f"  {len(output['library'])} books found")

# ── TOTAL LISTENING STATS ─────────────────────────────────────
print("Fetching total listening stats...")
try:
    stats = client.get(
        'stats/aggregates',
        monthly_listening_interval_duration=12,
        monthly_listening_interval_start_date=datetime.now().strftime('%Y-%m'),
        response_groups='total_listening_stats',
        locale='en_US',
        store='Audible'
    )
    output['total_stats'] = stats
    total_ms = stats.get('aggregated_total_listening_stats', {}).get('aggregated_sum', 0)
    print(f"  Total listening time: {round(total_ms/3600000, 1)} hours")
except Exception as e:
    print(f"  Error: {e}")
    output['total_stats'] = {}

# ── FINISHED BOOKS ────────────────────────────────────────────
print("Fetching finished books list...")
try:
    finished = client.get(
        'stats/status/finished',
        start_date='2000-01-01T00:00:00Z'
    )
    output['finished'] = finished.get('mark_as_finished_status_list', [])
    print(f"  {len(output['finished'])} finished records")
except Exception as e:
    print(f"  Error: {e}")
    output['finished'] = []

# ── WISHLIST ──────────────────────────────────────────────────
print("Fetching wishlist...")
try:
    wishlist = client.get(
        'wishlist',
        num_results=50,
        response_groups='product_attrs,product_desc'
    )
    output['wishlist'] = wishlist.get('products', [])
    print(f"  {len(output['wishlist'])} wishlist items")
except Exception as e:
    print(f"  Error: {e}")
    output['wishlist'] = []

# ── ACCOUNT ───────────────────────────────────────────────────
print("Fetching account info...")
try:
    account = client.get(
        'account/information',
        response_groups='subscription_details,plan_summary,customer_benefits'
    )
    output['account'] = account
except Exception as e:
    print(f"  Error: {e}")
    output['account'] = {}

# ── SAVE RAW DATA ─────────────────────────────────────────────
with open(OUTPUT_FILE, 'w') as f:
    json.dump(output, f, indent=2, default=str)
print(f"\nRaw data saved to: {OUTPUT_FILE}")

# ── SUMMARY ───────────────────────────────────────────────────
books = output['library']
total_ms = output.get('total_stats', {}).get('aggregated_total_listening_stats', {}).get('aggregated_sum', 0)
total_hours = round(total_ms / 3600000, 1)
finished_count = sum(1 for b in books if b.get('is_finished'))
not_started = sum(1 for b in books if b.get('percent_complete', 0) == 0.0)
in_progress = sum(1 for b in books if 0 < (b.get('percent_complete') or 0) < 100)

purchased_years = {}
for b in books:
    pd = str(b.get('purchase_date', '') or '')[:4]
    if pd:
        purchased_years[pd] = purchased_years.get(pd, 0) + 1

author_counts = {}
for b in books:
    for a in (b.get('authors') or []):
        name = a.get('name', '') if isinstance(a, dict) else ''
        if name:
            author_counts[name] = author_counts.get(name, 0) + 1

total_runtime = sum(b.get('runtime_length_min', 0) or 0 for b in books)
unfinished_hours = sum(
    (b.get('runtime_length_min', 0) or 0) * (1 - (b.get('percent_complete', 0) or 0) / 100)
    for b in books if not b.get('is_finished')
) / 60

print(f"\n{'=' * 60}")
print(f"SUMMARY")
print(f"{'=' * 60}")
print(f"Total books:              {len(books)}")
print(f"Finished:                 {finished_count}")
print(f"In progress:              {in_progress}")
print(f"Not started:              {not_started}")
print(f"Total hours listened:     {total_hours}h")
print(f"Total library runtime:    {round(total_runtime/60, 1)}h (if you listened to all)")
print(f"Unfinished backlog:       {round(unfinished_hours, 1)}h")

print(f"\nPurchases by year:")
for year in sorted(purchased_years):
    bar = '█' * purchased_years[year]
    print(f"  {year}: {bar} ({purchased_years[year]})")

print(f"\nTop 10 authors:")
for name, count in sorted(author_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {name}: {count} books")

print(f"\nTop 10 longest books:")
sorted_books = sorted(books, key=lambda x: x.get('runtime_length_min', 0) or 0, reverse=True)
for b in sorted_books[:10]:
    mins = b.get('runtime_length_min', 0) or 0
    status = '✓' if b.get('is_finished') else f"{b.get('percent_complete', 0)}%"
    print(f"  {b.get('title', '?')[:48]:<50} {round(mins/60, 1)}h  {status}")

print(f"\nDone. Open audible_dashboard_v2.html in a browser to see the full dashboard.")
