#!/usr/bin/env python3
"""SerpAPI search wrapper for CLI usage.

Usage:
    python3 serpapi_search.py --engine google --query "coffee"
    python3 serpapi_search.py --engine google_scholar --query "transformers" --param num=10
"""

import argparse
import json
import os
import sys

try:
    import serpapi
except ImportError:
    print("Error: 'serpapi' package not installed. Run: pip install serpapi", file=sys.stderr)
    sys.exit(1)


def parse_params(pairs: list[str] | None) -> dict:
    """Parse key=value pairs into a dict."""
    if not pairs:
        return {}
    result = {}
    for pair in pairs:
        if "=" not in pair:
            print(f"Warning: ignoring malformed param '{pair}' (expected key=value)", file=sys.stderr)
            continue
        k, v = pair.split("=", 1)
        result[k] = v
    return result


def main():
    parser = argparse.ArgumentParser(description="Search via SerpAPI")
    parser.add_argument("--engine", required=True, help="Search engine (google, bing, google_scholar, youtube, etc.)")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--param", action="append", help="Extra param as key=value (repeatable)")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("Error: SERPAPI_KEY environment variable not set.", file=sys.stderr)
        print("Get a free key at: https://serpapi.com/users/sign_up?plan=free", file=sys.stderr)
        sys.exit(1)

    client = serpapi.Client(api_key=api_key, timeout=args.timeout)

    # Engine-specific query param mapping
    query_param_map = {
        "youtube": "search_query",
        "yahoo": "p",
        "ebay": "_nkw",
        "apple_app_store": "term",
        "walmart": "query",
        "naver": "query",
    }
    query_key = query_param_map.get(args.engine, "q")

    params = {query_key: args.query, "engine": args.engine}
    params.update(parse_params(args.param))

    try:
        results = client.search(params)
        output = dict(results)

        dest = args.output
        if dest:
            with open(dest, "w") as f:
                json.dump(output, f, indent=2, default=str)
            print(f"Results written to {dest}", file=sys.stderr)
        else:
            json.dump(output, sys.stdout, indent=2, default=str)
            sys.stdout.write("\n")

    except serpapi.HTTPError as e:
        print(f"HTTP Error {e.status_code}: {e.error}", file=sys.stderr)
        sys.exit(1)
    except serpapi.TimeoutError as e:
        print(f"Timeout: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
