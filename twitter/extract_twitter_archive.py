"""
Extract and aggregate content data from a Twitter/X archive export.

Takes a Twitter archive zip file (or pre-extracted directory) and produces
a JSON file of pre-aggregated data suitable for embedding in an interactive
dashboard.

Usage:
    python extract_twitter_archive.py <path_to_archive_zip_or_dir> [output.json]

Output includes:
    - KPI totals (tweets, originals, retweets, media, URLs, unique counts)
    - Monthly and yearly volume breakdowns (original vs retweet)
    - Top 50 hashtags, mentions, and domains (overall and per-year top 20)
    - Top 20 tweets by likes and by retweets
    - Language distribution
    - Date range

Author: Colin Greenstreet / Claude (Anthropic)
Date: 17 February 2026
"""

import json
import sys
import zipfile
import tempfile
import os
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse


def load_twitter_js(filepath):
    """Load a Twitter archive .js file, stripping the window.YTD assignment prefix."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    json_start = content.index("[")
    return json.loads(content[json_start:])


def extract_archive(zip_path, extract_dir):
    """Extract a Twitter archive zip to a temporary directory."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    # Find the data/ directory (may be nested)
    for root, dirs, files in os.walk(extract_dir):
        if "tweets.js" in files:
            return root
    raise FileNotFoundError("Could not find tweets.js in archive")


def process_tweets(data_dir):
    """Process tweets.js and produce aggregated content data."""
    tweets = load_twitter_js(os.path.join(data_dir, "tweets.js"))

    # Accumulators
    all_hashtags = Counter()
    all_mentions = Counter()
    all_domains = Counter()
    lang_counts = Counter()
    monthly_volume = {}
    yearly_volume = {}
    hashtags_by_year = {}
    mentions_by_year = {}
    domains_by_year = {}
    records = []

    for t in tweets:
        tw = t["tweet"]
        dt = datetime.strptime(tw["created_at"], "%a %b %d %H:%M:%S %z %Y")
        year = str(dt.year)
        year_month = dt.strftime("%Y-%m")

        # Classification
        is_rt = tw["full_text"].startswith("RT @")
        has_media = (
            "extended_entities" in tw
            or len(tw.get("entities", {}).get("media", [])) > 0
        )

        # Hashtags
        hashtags = [
            h["text"].lower() for h in tw.get("entities", {}).get("hashtags", [])
        ]
        for h in hashtags:
            all_hashtags[h] += 1
            hashtags_by_year.setdefault(year, Counter())[h] += 1

        # Mentions
        mentions = [
            m["screen_name"]
            for m in tw.get("entities", {}).get("user_mentions", [])
        ]
        for m in mentions:
            all_mentions[m] += 1
            mentions_by_year.setdefault(year, Counter())[m] += 1

        # URLs and domains
        urls = tw.get("entities", {}).get("urls", [])
        url_count = 0
        for u in urls:
            expanded = u.get("expanded_url", u.get("url", ""))
            if expanded:
                try:
                    domain = urlparse(expanded).netloc.replace("www.", "")
                    if domain and "twitter.com" not in domain and "t.co" not in domain:
                        all_domains[domain] += 1
                        domains_by_year.setdefault(year, Counter())[domain] += 1
                        url_count += 1
                except Exception:
                    pass

        # Language
        lang_counts[tw.get("lang", "und")] += 1

        # Monthly volume
        monthly_volume.setdefault(
            year_month, {"total": 0, "original": 0, "retweet": 0}
        )
        monthly_volume[year_month]["total"] += 1
        if is_rt:
            monthly_volume[year_month]["retweet"] += 1
        else:
            monthly_volume[year_month]["original"] += 1

        # Yearly volume
        yearly_volume.setdefault(
            year,
            {
                "total": 0,
                "original": 0,
                "retweet": 0,
                "with_media": 0,
                "favorites": 0,
                "retweet_count": 0,
            },
        )
        yearly_volume[year]["total"] += 1
        if is_rt:
            yearly_volume[year]["retweet"] += 1
        else:
            yearly_volume[year]["original"] += 1
        if has_media:
            yearly_volume[year]["with_media"] += 1
        yearly_volume[year]["favorites"] += int(tw.get("favorite_count", 0))
        yearly_volume[year]["retweet_count"] += int(tw.get("retweet_count", 0))

        records.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "text": tw["full_text"][:200],
                "favorites": int(tw.get("favorite_count", 0)),
                "retweets": int(tw.get("retweet_count", 0)),
                "is_retweet": is_rt,
                "has_media": has_media,
                "url_count": url_count,
            }
        )

    # Compute totals
    total = len(records)
    originals = sum(1 for r in records if not r["is_retweet"])
    with_media = sum(1 for r in records if r["has_media"])
    with_urls = sum(1 for r in records if r["url_count"] > 0)

    # Top tweets
    top_by_fav = sorted(records, key=lambda x: x["favorites"], reverse=True)[:20]
    top_by_rt = sorted(records, key=lambda x: x["retweets"], reverse=True)[:20]

    # Date range
    dates = [
        datetime.strptime(tw["tweet"]["created_at"], "%a %b %d %H:%M:%S %z %Y")
        for tw in tweets
    ]
    dates.sort()

    # Build output
    output = {
        "total_tweets": total,
        "original_tweets": originals,
        "retweets": total - originals,
        "with_media": with_media,
        "with_urls": with_urls,
        "unique_hashtags": len(all_hashtags),
        "unique_mentions": len(all_mentions),
        "date_range": {
            "start": dates[0].strftime("%Y-%m-%d"),
            "end": dates[-1].strftime("%Y-%m-%d"),
        },
        "top_hashtags": [
            {"tag": h, "count": c} for h, c in all_hashtags.most_common(50)
        ],
        "top_mentions": [
            {"account": m, "count": c} for m, c in all_mentions.most_common(50)
        ],
        "top_domains": [
            {"domain": d, "count": c} for d, c in all_domains.most_common(50)
        ],
        "languages": [
            {"lang": l, "count": c} for l, c in lang_counts.most_common(20)
        ],
        "monthly_volume": monthly_volume,
        "yearly_volume": yearly_volume,
        "hashtags_by_year": {
            y: [{"tag": h, "count": c} for h, c in counter.most_common(20)]
            for y, counter in hashtags_by_year.items()
        },
        "mentions_by_year": {
            y: [{"account": m, "count": c} for m, c in counter.most_common(20)]
            for y, counter in mentions_by_year.items()
        },
        "domains_by_year": {
            y: [{"domain": d, "count": c} for d, c in counter.most_common(20)]
            for y, counter in domains_by_year.items()
        },
        "top_tweets_by_favorites": [
            {
                "date": r["date"],
                "text": r["text"],
                "favorites": r["favorites"],
                "retweets": r["retweets"],
            }
            for r in top_by_fav
        ],
        "top_tweets_by_retweets": [
            {
                "date": r["date"],
                "text": r["text"],
                "favorites": r["favorites"],
                "retweets": r["retweets"],
            }
            for r in top_by_rt
        ],
    }

    return output


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <archive_zip_or_dir> [output.json]")
        sys.exit(1)

    source = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "dashboard_data.json"

    if os.path.isfile(source) and source.endswith(".zip"):
        with tempfile.TemporaryDirectory() as tmp:
            print(f"Extracting {source}...")
            data_dir = extract_archive(source, tmp)
            print(f"Processing tweets from {data_dir}...")
            result = process_tweets(data_dir)
    elif os.path.isdir(source):
        # Assume data/ subdirectory or direct path to tweets.js directory
        if os.path.exists(os.path.join(source, "tweets.js")):
            data_dir = source
        elif os.path.exists(os.path.join(source, "data", "tweets.js")):
            data_dir = os.path.join(source, "data")
        else:
            print("Error: Could not find tweets.js in the specified directory")
            sys.exit(1)
        print(f"Processing tweets from {data_dir}...")
        result = process_tweets(data_dir)
    else:
        print(f"Error: {source} is not a valid zip file or directory")
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Dashboard data written to {output_path}")
    print(f"  Total tweets: {result['total_tweets']:,}")
    print(f"  Date range: {result['date_range']['start']} to {result['date_range']['end']}")
    print(f"  Unique hashtags: {result['unique_hashtags']}")
    print(f"  Unique mentions: {result['unique_mentions']}")
    print(f"  JSON size: {os.path.getsize(output_path):,} bytes")


if __name__ == "__main__":
    main()
