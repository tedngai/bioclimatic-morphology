# xAI X Search Tool Reference

Docs: https://docs.x.ai/developers/tools/x-search

## Concept
`x_search` is an xAI tool that lets Grok models query live X (Twitter) data. You enable it inside the Responses/Chat API by listing the tool and optional parameters. xAI runs the search server-side and returns structured posts with metadata/citations.

## Authentication
- Base URL: `https://api.x.ai/v1`
- Header: `Authorization: Bearer $XAI_API_KEY`
- Models: Reasoning or non-reasoning Grok variants (e.g., `grok-4.20-beta-latest-non-reasoning`).

## Basic Request (cURL)
```bash
curl https://api.x.ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4.20-beta-latest-non-reasoning",
    "input": [{"role": "user", "content": "Collect the latest news on frontier AI"}],
    "tools": [{"type": "x_search"}]
  }'
```

## Tool Parameters
| Field | Type | Notes |
| --- | --- | --- |
| `allowed_x_handles` | string[] | Only include posts from these handles (max 10). Mutually exclusive with `excluded_x_handles`. |
| `excluded_x_handles` | string[] | Omit handles. |
| `from_date` / `to_date` | date/string | Filter timeframe (ISO `YYYY-MM-DD` or datetime). |
| `enable_image_understanding` | bool | Ask Grok to analyze images attached to posts. |
| `enable_video_understanding` | bool | Same for videos. |

Python SDK example:
```python
from datetime import datetime
from xai_sdk import Client
from xai_sdk.tools import x_search
from xai_sdk.chat import user

client = Client(api_key=os.environ["XAI_API_KEY"])
chat = client.chat.create(
    model="grok-4.20-beta-latest-non-reasoning",
    tools=[x_search(from_date=datetime(2026, 3, 1), allow_x_handles=["elonmusk"])]
)
chat.append(user("Summarize reactions to Sora"))
response = chat.run()
print(response.output[0].content)
```

## Usage Tips
- Results arrive as tool calls + citations. Always surface handles, timestamps, and URLs when summarizing.
- Combine with other tools (e.g., `web_search`) when cross-referencing X chatter with broader web coverage.
- If you need raw tweet IDs, parse them from the tool output before storing in research notes.
- Rate limits follow your xAI plan; monitor tool invocation counts in console.x.ai.
