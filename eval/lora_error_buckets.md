# Baseline Error Buckets

This file groups baseline failures by the first point of failure in the production-style pipeline.

## Bucket counts

- SCHEMA_FAIL_INVALID_ENUM: 2
- WRONG_TOOL: 3

## Example failures (up to 2 per bucket)

### SCHEMA_FAIL_INVALID_ENUM
- id: ex06
  - input: Office internet is down for multiple people. No one can load any websites right now.
  - raw_output: {\n  "tool_name": "create_support_ticket",\n  "arguments": {\n    "product": "internet",\n    "category": "outage",\n    "severity": "critical",\n    "summary": "Office internet is down for multiple people. No one can load any websites right now.",\n    "description": "The office's internet connection has been compromised, causing issues with website loading for multiple users. This is a critical issue that needs immediate attention.",\n    "os": "unknown",\n    "user_email": "no_user_email"\n  }\n}
- id: ex08
  - input: I was charged twice for this month’s subscription. Please refund the duplicate charge.
  - raw_output: {\n  "tool_name": "create_support_ticket",\n  "arguments": {\n    "product": "subscription",\n    "category": "outage",\n    "severity": "critical",\n    "summary": "Subscription charges duplicated",\n    "description": "The customer has been charged twice for the same month's subscription.",\n    "os": "unknown",\n    "user_email": "customer@example.com"\n  }\n}

### WRONG_TOOL
- id: ex02
  - input: It keeps crashing every time I open it. Please fix ASAP.
  - raw_output: {\n  "tool_name": "create_support_ticket",\n  "arguments": {\n    "product": "vpn",\n    "category": "bug",\n    "severity": "high",\n    "summary": "The application crashes every time I open it.",\n    "description": "I have tried to troubleshoot this issue but haven't been able to resolve it.",\n    "os": "unknown",\n    "user_email": "user@example.com"\n  }\n}
- id: ex03
  - input: Email is not syncing on my iPhone since yesterday. No new messages are coming in.
  - raw_output: {\n  "tool_name": "NEED_INFO",\n  "arguments": {\n    "missing": ["product", "category", "severity", "summary", "description", "os", "user_email"]\n  }\n}

