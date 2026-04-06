---
name: gemini-deep-research
description: Run deep, multi-step research tasks using Google's Gemini Deep Research API agent. Produces detailed cited Markdown reports by autonomously searching the web, reading sources, and synthesizing findings. Use when a user asks for in-depth research, comprehensive topic analysis, literature reviews, competitive landscapes, or any query that benefits from extended autonomous web research beyond a single search. Triggers on phrases like "deep research", "research report", "comprehensive analysis", "deep dive into", "investigate thoroughly", or when research scope clearly exceeds what a single web search can cover.
---

# Gemini Deep Research

## Overview
Gemini Deep Research is an async API agent (`deep-research-pro-preview-12-2025`) that autonomously plans, searches, reads, and synthesizes multi-step research into detailed cited Markdown reports. Tasks take 1–5 minutes.

## Quick Start
Run the bundled script to execute a research task end-to-end:
```bash
scripts/deep_research.sh "Research the history of Google TPUs"
```
The script handles starting the task, polling, and outputting the final report.

## Workflow

### 1. Simple Research Query
Use the script directly. It requires `GEMINI_API_KEY` in the environment and `jq` installed.
```bash
scripts/deep_research.sh "<research query>" [poll_interval_seconds]
```
Default poll interval is 10 seconds.

### 2. Structured/Formatted Reports
Append formatting instructions directly in the query string:
```bash
scripts/deep_research.sh "Research the competitive landscape of EV batteries.

Format as:
1. Executive Summary
2. Key Players (include comparison table)
3. Supply Chain Risks
4. Sources"
```

### 3. Manual API Calls (for multimodal or advanced use)
When the query includes images, PDFs, or needs file search, use curl directly. See [references/api.md](references/api.md) for full endpoint docs, multimodal input format, and file search integration.

## Output Handling
- Output is Markdown with inline citations — ideal for Obsidian
- Save reports: pipe script output to a file (`> report.md`)
- For long reports, save to the workspace and share a summary with the user

## Operational Notes
- `background: true` is mandatory — the API only works async
- Tasks typically take 1–5 minutes; be patient with polling
- Poll every 10s (default); don't hammer the endpoint
- The agent has built-in `google_search` and `url_context` tools
- Multimodal inputs (images, PDFs, audio, video) are supported via the REST API directly
