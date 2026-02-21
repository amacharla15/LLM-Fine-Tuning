# Baseline Error Buckets

This file groups baseline failures by the first point of failure in the production-style pipeline.

## Bucket counts

- SCHEMA_FAIL_INVALID_ENUM: 3
- WRONG_TOOL: 3

## Example failures (up to 2 per bucket)

### SCHEMA_FAIL_INVALID_ENUM
- id: ex05
  - input: I can’t reset my password. The reset link says it’s expired immediately.
  - raw_output: {\n  "tool_name": "create_support_ticket",\n  "arguments": {\n    "product": "account",\n    "category": "password",\n    "severity": "critical",\n    "summary": "Account password reset failed",\n    "description": "The reset link has expired immediately.",\n    "os": "unknown"\n  }\n}
- id: ex06
  - input: Office internet is down for multiple people. No one can load any websites right now.
  - raw_output: {\n  "tool_name": "create_support_ticket",\n  "arguments": {\n    "product": "internet",\n    "category": "outage",\n    "severity": "critical",\n    "summary": "Office internet is down for multiple people. No one can load any websites right now.",\n    "description": "The office's internet connection has been compromised, causing issues with website loading for multiple users. This is a critical issue that needs immediate attention.",\n    "os": "unknown",\n    "user_email": "unknown"\n  }\n}

### WRONG_TOOL
- id: ex02
  - input: It keeps crashing every time I open it. Please fix ASAP.
  - raw_output: {\n  "tool_name": "create_support_ticket",\n  "arguments": {\n    "product": "laptop",\n    "category": "bug",\n    "severity": "high",\n    "summary": "The laptop crashes every time I open it.",\n    "description": "I have tried to troubleshoot this issue but it persists. The laptop crashes when I attempt to access any settings or perform any operations.",\n    "os": "unknown",\n    "user_email": ""\n  }\n}
- id: ex03
  - input: Email is not syncing on my iPhone since yesterday. No new messages are coming in.
  - raw_output: {\n  "tool_name": "NEED_INFO",\n  "arguments": {\n    "missing": ["product", "category", "severity", "summary", "description", "os", "user_email"]\n  }\n}

