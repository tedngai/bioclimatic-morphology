# Gemini Deep Research API Reference

## Base URL
```
https://generativelanguage.googleapis.com/v1beta
```

## Authentication
All requests require: `-H "x-goog-api-key: $GEMINI_API_KEY"`

## Agent ID
```
deep-research-pro-preview-12-2025
```

## Endpoints

### Start Research Task
```
POST /interactions
```
**Body:**
```json
{
  "input": "Research query string",
  "agent": "deep-research-pro-preview-12-2025",
  "background": true
}
```

**Multimodal input** (images, PDFs, audio, video):
```json
{
  "input": [
    {"type": "text", "text": "Analyze this and research..."},
    {"type": "image", "uri": "https://example.com/photo.jpg"}
  ],
  "agent": "deep-research-pro-preview-12-2025",
  "background": true
}
```

**With File Search (your own data):**
```json
{
  "tools": [
    {
      "type": "file_search",
      "file_search_store_names": ["fileSearchStores/my-store-name"]
    }
  ]
}
```

**Response:**
```json
{
  "id": "interaction-id",
  "status": "in_progress",
  ...
}
```

### Poll for Results
```
GET /interactions/{interaction_id}
```

**Response (completed):**
```json
{
  "id": "interaction-id",
  "status": "completed",
  "outputs": [
    {"text": "# Full research report in markdown..."}
  ]
}
```

**Response (failed):**
```json
{
  "id": "interaction-id",
  "status": "failed",
  "error": "error message"
}
```

### Status Values
| Status | Meaning |
|--------|---------|
| `in_progress` | Still researching |
| `completed` | Report ready in `outputs[-1].text` |
| `failed` | Error occurred |

## Steerability
Include formatting instructions directly in the input text:
```
Research X.

Format the output as:
1. Executive Summary
2. Key Findings (include data tables)
3. Analysis
4. Sources
```

## Notes
- Research tasks are async-only (`background: true` required)
- Tasks typically take 1-5 minutes
- Poll interval: 10 seconds recommended
- Output is Markdown with inline citations
- Supports multimodal inputs (images, PDFs, audio, video)
