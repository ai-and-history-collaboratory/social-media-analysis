# Social Media Analysis

Interactive dashboards and extraction tools for analysing social media archives using AI-assisted workflows. Part of the [AI + History Collaboratory](https://github.com/ai-and-history-collaboratory).

## What this demonstrates

Social media archives — Twitter/X exports, Bluesky archives, and others — contain rich structured data about scholarly communities, research networks, and the evolution of academic projects over time. This repository shows how AI agents can transform raw archive exports into interactive analytical dashboards, with no manual data cleaning or coding required.

Each analysis includes:

- **An extraction script** — Python code that parses the platform's export format and produces pre-aggregated JSON
- **An interactive dashboard** — a self-contained HTML file (Chart.js) with filters, charts, and sortable tables
- **The aggregated data** — JSON files suitable for further analysis or reuse

## Twitter / X

The first analysis covers the [@Marinelivesorg](https://x.com/Marinelivesorg) Twitter account (est. July 2012), which has been the public voice of the MarineLives project for over a decade.

**[View all dashboards →](https://ai-and-history-collaboratory.github.io/social-media-analysis/)**

Two dashboards are available:

- **[Content Explorer](https://ai-and-history-collaboratory.github.io/social-media-analysis/twitter/)** — volume trends, hashtags, mentions, domains, content mix, and top tweets with year filtering
- **[Project Biography: Topic Evolution](https://ai-and-history-collaboratory.github.io/social-media-analysis/twitter/topics.html)** — quarterly NMF topic modelling showing how the project's thematic focus shifted over thirteen years

### Summary statistics

| Metric | Value |
|--------|-------|
| Total tweets | 10,535 |
| Original tweets | 10,142 (96.3%) |
| Date range | July 2012 – June 2025 |
| Unique hashtags | 249 |
| Unique accounts mentioned | 1,402 |
| Unique domains shared | 363 |
| Tweets with media | 3,428 |

### Dashboard features

- **Year filter** — slice all charts and KPIs by individual year
- **Monthly tweet volume** — line chart showing original tweets vs retweets over time
- **Yearly activity overview** — stacked bar chart of activity per year
- **Top 20 hashtags, mentions, and domains** — horizontal bar charts, updating with the year filter
- **Content mix** — doughnut chart showing media, URL-only, and text-only proportions
- **Top tweets** — sortable tables by likes and by retweets

### Files

| File | Purpose |
|------|---------|
| `index.html` | Landing page linking to all dashboards |
| `twitter/index.html` | Content Explorer dashboard (self-contained, no server required) |
| `twitter/topics.html` | Project Biography: Topic Evolution dashboard |
| `twitter/extract_twitter_archive.py` | Python script to extract and aggregate data from a Twitter archive |
| `twitter/dashboard_data.json` | Pre-aggregated JSON data powering the Content Explorer |

### Reproducing the analysis

1. Request your Twitter/X archive from Settings → Your Account → Download an archive of your data
2. Run the extraction script:

```bash
python twitter/extract_twitter_archive.py path/to/twitter-archive.zip twitter/dashboard_data.json
```

3. The script produces `dashboard_data.json`. To update the dashboard, replace the `const DATA = {...}` block in `index.html` with the contents of the new JSON file.

## Planned additions

- Bluesky archive analysis
- LinkedIn post analysis
- Cross-platform comparison dashboards

## About

This repository is maintained by [Colin Greenstreet](https://github.com/Addaci) as part of the **AI + History Collaboratory**, an initiative exploring how AI tools can support historical research workflows.

The dashboards and extraction scripts were created collaboratively with [Claude](https://claude.ai) (Anthropic) using Claude's Cowork mode, and Anthropic Data plugin commands for data exploration and dashboard creation.

## Licence

Content and code in this repository are released under the [MIT Licence](LICENSE).
