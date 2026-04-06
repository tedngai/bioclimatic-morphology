---
name: serpapi-search
description: >
  Search the web using SerpAPI for structured results across Google, Bing, YouTube, Google Scholar,
  DuckDuckGo, and other engines. Use when real-time web research needs structured, high-quality results
  beyond what basic web search provides — especially for academic papers (Google Scholar), product
  comparisons (Google Shopping), YouTube video searches, or multi-engine queries. Triggers on phrases
  like "search with serpapi", "google scholar search", "structured web search", or when specific
  SerpAPI engines are requested.
---

# SerpAPI Search

## Prerequisites

1. API key: set `SERPAPI_KEY` in the environment (get one free at https://serpapi.com/users/sign_up?plan=free)
2. Python package: `pip install serpapi` (run once)

## Quick Start

```bash
python3 <skill_dir>/scripts/serpapi_search.py --engine google --query "coffee"
```

Output is JSON to stdout. Pipe through `jq` for pretty-printing:

```bash
python3 <skill_dir>/scripts/serpapi_search.py --engine google_scholar --query "transformer architecture" | jq '.organic_results[:5]'
```

## Supported Engines

| Engine | Key param | Use case |
|---|---|---|
| `google` | `q` | General web search |
| `bing` | `q` | Alternative web search |
| `google_scholar` | `q` | Academic papers & citations |
| `youtube` | `search_query` | Video search |
| `duckduckgo` | `q` | Privacy-focused search |
| `google_shopping` | `q` | Product search & comparison |
| `google_maps` | `q` | Local businesses & maps |
| `google_events` | `q` | Events in a location |
| `ebay` | `_nkw` | eBay listings |
| `yahoo` | `p` | Yahoo search |
| `baidu` | `q` | Baidu search |
| `apple_app_store` | `term` | App Store search |
| `walmart` | `query` | Walmart products |
| `home_depot` | `q` | Home Depot products |

For full engine list see: https://serpapi.com/search-api

## Usage Patterns

### Basic search
```bash
python3 scripts/serpapi_search.py --engine google --query "latest AI models 2026"
```

### Academic research
```bash
python3 scripts/serpapi_search.py --engine google_scholar --query "attention mechanism transformers"
```

### With filters
Pass extra params via `--param key=value`:
```bash
python3 scripts/serpapi_search.py --engine google --query "coffee" --param gl=us --param hl=en --param num=10
```

### Extracting specific fields
Use jq on output:
- Top organic results: `jq '.organic_results[:5]'`
- Answer box: `jq '.answer_box'`
- Knowledge graph: `jq '.knowledge_graph'`
- Related searches: `jq '.related_searches'`

## Error Handling

- **401**: Invalid or missing SERPAPI_KEY
- **429**: Rate limit exceeded (free tier: 100 searches/month)
- **Timeout**: Increase with `--timeout <seconds>` (default: 30)

## Tips

- For research deep-dives, combine multiple engines (Google + Google Scholar) for breadth + depth
- Free tier is limited — use `num` param to reduce result counts when possible
- Results are cached by SerpAPI server-side, repeated queries are fast
