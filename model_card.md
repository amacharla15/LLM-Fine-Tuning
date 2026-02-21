# Model Card — Ticket Tool-Call JSON (LoRA Adapter)

Base model: Qwen/Qwen2.5-0.5B-Instruct
Method: LoRA (PEFT) supervised fine-tuning to output schema-valid tool-call JSON

## Intended use
Convert support-issue text into exactly one JSON tool call that validates against:
- schemas/create_support_ticket.schema.json
- schemas/need_info.schema.json

## Not intended use
Open-ended chat, high-stakes decision making, or production deployment without additional safeguards.

## Limitations
Tool selection errors can still occur (WRONG_TOOL bucket remains).
Enum mapping can still fail on edge phrases.
Gold eval set is small (N=10) and mainly serves as a consistent before/after check.

## Evaluation
See eval/baseline_metrics.json and eval/lora_metrics.json
