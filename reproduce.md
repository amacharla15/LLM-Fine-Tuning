# Reproduce

## Phase 0
- schemas/create_support_ticket.schema.json
- schemas/need_info.schema.json
- eval/10_gold_examples.jsonl

## Phase 1 (baseline)
python eval/run_baseline.py
python eval/score_baseline.py

Outputs:
- eval/baseline_predictions.jsonl
- eval/baseline_metrics.json
- eval/error_buckets.md

## Phase 2 (data)
python data/generate_dataset.py
python data/sanity_check.py

Outputs:
- data/train.jsonl
- data/val.jsonl
- data/test.jsonl

## Phase 3 (LoRA train)
python train/train_lora_sft.py

Adapter output:
- adapters/lora_sft_small_wsl_gpu/

## Phase 4 (LoRA eval)
python eval/run_lora_eval.py
python eval/score_lora.py

Outputs:
- eval/lora_predictions.jsonl
- eval/lora_metrics.json
- eval/lora_error_buckets.md
