# LoRA Fine-tuning for Reliable Support Ticket Tool-Call JSON

This project fine-tunes a small instruct model with LoRA to emit schema-valid tool-call JSON for support ticket creation.

## Production idea
In Slack/Teams support bots, the LLM must output strict JSON that a backend validates before calling a ticket API (Jira/ServiceNow/Zendesk). If required info is missing, the model should return NEED_INFO instead of guessing.

## Tools + schemas
- tools: create_support_ticket, NEED_INFO
- schemas:
  - schemas/create_support_ticket.schema.json
  - schemas/need_info.schema.json

## Key folders
- schemas/ : JSON schema contract
- eval/ : gold set, predictions, metrics, error buckets
- data/ : dataset generator + train/val/test
- train/ : LoRA SFT training script
- adapters/ : saved LoRA adapters

## Results (gold eval N=10)
Baseline (Qwen/Qwen2.5-0.5B-Instruct):
- strict_json_rate: 1.0
- schema_valid_rate: 0.7
- tool_name_accuracy_on_schema_valid: 0.5714
- error buckets: WRONG_TOOL=3, SCHEMA_FAIL_INVALID_ENUM=3

LoRA (trained on 200 train / 50 val, 1 epoch, GPU):
- strict_json_rate: 1.0
- schema_valid_rate: 0.8
- tool_name_accuracy_on_schema_valid: 0.625
- error buckets: WRONG_TOOL=3, SCHEMA_FAIL_INVALID_ENUM=2

See:
- eval/baseline_metrics.json
- eval/lora_metrics.json
- eval/error_buckets.md
- eval/lora_error_buckets.md

## Reproduce
See reproduce.md
