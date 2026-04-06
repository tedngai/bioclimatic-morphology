---
name: xai-x-search
description: Enable and operate xAI's `x_search` tool to pull real-time X/Twitter posts, user activity, and threads inside Grok model calls. Use this skill whenever research requires up-to-the-minute social chatter or citations from X via the xAI Responses/Chat API.
---

# xAI X Search

## Overview
The `x_search` tool lets Grok models query X (Twitter) directly while responding to prompts. You declare the tool (and optional filters) when calling `POST /v1/responses` or the xAI SDK, and the API streams back tool outputs + citations you can quote in research notes.

Reference cheat sheet: [references/api.md](references/api.md)

## Quick Start
1. **API key**: Store as `XAI_API_KEY` (console.x.ai → API keys).
2. **Model**: Use a Grok reasoning model (e.g., `grok-4.20-beta-latest-non-reasoning`).
3. **Enable tool**: Add `{ "type": "x_search" }` to the `tools` array of your request.
4. **Optional filters**: Provide tool arguments (handles, date range) either inline or via SDK helper.

## Common Workflows

### 1. Open-ended Sentiment Scan
Use when you just need “What is X saying about …?”
1. Send the user question as-is.
2. Attach `x_search` with no filters; Grok will fetch recent, relevant posts.
3. Extract the tool output (posts usually include handle, timestamp, text, URL). Quote top items with citations.

### 2. Handle-Scoped Monitoring
1. Set `allowed_x_handles` to focus on official accounts (max 10 handles).
2. Optionally add `from_date`/`to_date` for event windows.
3. Ask Grok to summarize differences or highlight notable posts.

### 3. Excluding Noise
1. Use `excluded_x_handles` for spammy accounts.
2. Combine with `enable_image_understanding`/`enable_video_understanding` when visual memes matter.

### 4. Thread / Event Deep Dive
1. Prompt the model with context (e.g., “compile the key takeaways from the latest OpenAI thread”).
2. Provide handle filter + narrow date range to keep the result focused.
3. Request explicit citations (Grok typically emits them automatically; restate that requirement in your prompt for reliability).

## Implementation Notes
- Parse tool calls from the `response.output` stream; they include structured JSON of posts.
- Always surface handle, timestamp, and canonical post URL in research deliverables.
- Respect user privacy rules—only cite public content and avoid storing sensitive data beyond research needs.
- See [references/api.md](references/api.md) for parameter descriptions and SDK snippets.
