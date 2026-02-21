# Dataset Card — Ticket Tool-Call JSON (Phase 2)

## Goal
Train an instruct model to output schema-valid tool-call JSON for:
- create_support_ticket
- NEED_INFO

This dataset targets the two baseline failure modes:
1) invalid enum values (e.g., "internet", "password", "urgent")
2) wrong tool selection (ticket creation vs NEED_INFO)

## Format (JSONL)
Each line:
- id: string
- input: user utterance
- output: a single JSON object matching Phase 0 schemas

Example:
{"id":"tr_000001","input":"VPN disconnects every 5 minutes on my Mac. Urgent.","output":{"tool_name":"create_support_ticket","arguments":{...}}}

## Splits
- train: 80%
- val: 10%
- test: 10%

## Data sources
- Synthetic templates with controlled noise (70–80%)
- Hand-checked set for realism (20–30%): data/hand_checked/hand_fixme.jsonl

## Label rules
- Enum normalization:
  - "internet"/"wifi"/"LAN" -> product="network"
  - "password reset"/"login"/"access denied" -> category="access"
  - urgency words ("ASAP", "urgent") influence severity only if product/category are clear
- Abstain:
  - if product is unclear -> NEED_INFO missing includes "product"
  - NEVER output user_email unless a valid email is present
