# Hand-checked set (Phase 2)

Goal: make the dataset believable and reduce synthetic artifacts.

Workflow:
1) Copy 50–200 examples from data/train.jsonl into hand_fixme.jsonl
2) Manually rewrite the input text to sound more human (keep the output labels)
3) Optional: add a few tricky real-world variations (typos, partial info, multi-symptom)

Only edit "input". Keep "output" schema-valid.
