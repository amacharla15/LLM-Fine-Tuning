# Phase 0 Metrics + Scoring Rules (Frozen Contract)

## Output Contract (Hard Rules)
A model output is considered usable ONLY if:
1) Output is exactly one JSON object (after trimming whitespace).
2) Top-level keys are exactly: tool_name, arguments.
3) tool_name ∈ {"create_support_ticket","NEED_INFO"}.
4) The JSON validates against one of the two schemas:
   - schemas/create_support_ticket.schema.json
   - schemas/need_info.schema.json

If any of the above fails, the output is a FAILURE for downstream automation.

## Primary Metrics (Pass/Fail)
For a dataset of N examples:

### 1) strict_json_rate
% outputs that parse as exactly one JSON object with no extra text.

### 2) schema_valid_rate
% outputs that pass JSON Schema validation against either schema.

### 3) tool_name_accuracy (on schema-valid outputs)
% outputs where tool_name matches gold tool_name.

## Tool-Specific Metrics (on schema-valid + correct tool_name)

### A) create_support_ticket enum_accuracy
For examples where gold tool is create_support_ticket:
- product_accuracy: exact match
- category_accuracy: exact match
- severity_accuracy: exact match

(summary/description are NOT exact-matched; they are checked only for schema constraints.)

### B) NEED_INFO missing_set_accuracy
For examples where gold tool is NEED_INFO:
- missing_set_accuracy: predicted missing set == gold missing set (exact set match)

## Notes / Clarifications (Frozen)
- If user_email is not explicitly present in input, it should be omitted.
- If os is not explicitly present, it may be omitted.
- The model should choose NEED_INFO when required fields cannot be confidently derived from the user text.
