import json
import os

from jsonschema import Draft7Validator


def read_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s == "":
                continue
            rows.append(json.loads(s))
    return rows


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_single_json_object(raw_output):
    s = raw_output.strip()

    # Hard fail: code fences almost always mean extra text
    if s.startswith("```"):
        return (False, None, None, "EXTRA_TEXT_CODE_FENCE")

    first = s.find("{")
    last = s.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return (False, None, None, "NO_JSON_BRACES")

    prefix = s[:first].strip()
    suffix = s[last + 1:].strip()

    strict_json_only = (prefix == "" and suffix == "")

    candidate = s[first:last + 1]
    try:
        obj = json.loads(candidate)
    except Exception:
        if strict_json_only:
            return (False, None, candidate, "JSON_PARSE_FAIL")
        return (False, None, candidate, "EXTRA_TEXT_AND_PARSE_FAIL")

    if not isinstance(obj, dict):
        return (False, None, candidate, "JSON_NOT_OBJECT")

    if strict_json_only:
        return (True, obj, candidate, None)

    # Still parseable but has extra text
    return (False, obj, candidate, "EXTRA_TEXT")


def schema_validate(obj, v_create, v_need):
    # returns: (is_valid, which_schema, error_bucket)
    errors_create = list(v_create.iter_errors(obj))
    if len(errors_create) == 0:
        return (True, "create_support_ticket", None)

    errors_need = list(v_need.iter_errors(obj))
    if len(errors_need) == 0:
        return (True, "NEED_INFO", None)

    # pick the "best" error to bucket: prefer enum/required
    best = None
    all_errs = []
    i = 0
    while i < len(errors_create):
        all_errs.append(errors_create[i])
        i += 1
    i = 0
    while i < len(errors_need):
        all_errs.append(errors_need[i])
        i += 1

    i = 0
    while i < len(all_errs):
        e = all_errs[i]
        if best is None:
            best = e
        else:
            # enum/required more informative
            pr_best = 2
            pr_e = 2
            if best.validator == "enum" or best.validator == "required":
                pr_best = 0
            elif best.validator == "additionalProperties":
                pr_best = 1
            if e.validator == "enum" or e.validator == "required":
                pr_e = 0
            elif e.validator == "additionalProperties":
                pr_e = 1
            if pr_e < pr_best:
                best = e
        i += 1

    if best is None:
        return (False, None, "SCHEMA_FAIL_OTHER")

    if best.validator == "required":
        return (False, None, "SCHEMA_FAIL_MISSING_REQUIRED")
    if best.validator == "enum":
        return (False, None, "SCHEMA_FAIL_INVALID_ENUM")
    if best.validator == "additionalProperties":
        return (False, None, "SCHEMA_FAIL_EXTRA_KEYS")

    return (False, None, "SCHEMA_FAIL_OTHER")


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    pred_path = os.path.join(repo_root, "eval", "lora_predictions.jsonl")
    gold_path = os.path.join(repo_root, "eval", "10_gold_examples.jsonl")
    schema_create_path = os.path.join(repo_root, "schemas", "create_support_ticket.schema.json")
    schema_need_path = os.path.join(repo_root, "schemas", "need_info.schema.json")
    metrics_out = os.path.join(repo_root, "eval", "lora_metrics.json")
    buckets_out = os.path.join(repo_root, "eval", "lora_error_buckets.md")

    preds = read_jsonl(pred_path)
    gold = read_jsonl(gold_path)

    gold_map = {}
    i = 0
    while i < len(gold):
        gold_map[gold[i]["id"]] = gold[i]["gold"]
        i += 1

    schema_create = load_json(schema_create_path)
    schema_need = load_json(schema_need_path)

    v_create = Draft7Validator(schema_create)
    v_need = Draft7Validator(schema_need)

    total = len(preds)

    strict_json_pass = 0
    schema_valid_pass = 0

    tool_correct_count = 0

    # create_support_ticket field accuracies (only when schema-valid + tool-correct + gold tool matches)
    create_total = 0
    product_correct = 0
    category_correct = 0
    severity_correct = 0

    # NEED_INFO missing-set accuracy (only when schema-valid + tool-correct + gold tool matches)
    need_total = 0
    missing_set_correct = 0

    bucket_counts = {}
    bucket_examples = {}

    idx = 0
    while idx < len(preds):
        row = preds[idx]
        ex_id = row["id"]
        raw_output = row["raw_output"]

        gold_obj = gold_map.get(ex_id, None)
        if gold_obj is None:
            idx += 1
            continue

        gold_tool = gold_obj.get("tool_name", None)

        strict_ok, parsed_obj, candidate_json, parse_bucket = extract_single_json_object(raw_output)

        if strict_ok:
            strict_json_pass += 1

        # If strict_ok is False and we have a parse_bucket, bucket it now,
        # BUT still attempt schema validation if parsed_obj exists (extra text case).
        if not strict_ok and parse_bucket is not None:
            bucket_counts[parse_bucket] = bucket_counts.get(parse_bucket, 0) + 1
            if parse_bucket not in bucket_examples:
                bucket_examples[parse_bucket] = []
            if len(bucket_examples[parse_bucket]) < 2:
                bucket_examples[parse_bucket].append(
                    {"id": ex_id, "input": row["input"], "raw_output": raw_output}
                )

        if parsed_obj is None:
            idx += 1
            continue

        is_schema_valid, which_schema, schema_bucket = schema_validate(parsed_obj, v_create, v_need)
        if not is_schema_valid:
            bucket_counts[schema_bucket] = bucket_counts.get(schema_bucket, 0) + 1
            if schema_bucket not in bucket_examples:
                bucket_examples[schema_bucket] = []
            if len(bucket_examples[schema_bucket]) < 2:
                bucket_examples[schema_bucket].append(
                    {"id": ex_id, "input": row["input"], "raw_output": raw_output, "parsed": parsed_obj}
                )
            idx += 1
            continue

        schema_valid_pass += 1

        pred_tool = parsed_obj.get("tool_name", None)
        if pred_tool != gold_tool:
            b = "WRONG_TOOL"
            bucket_counts[b] = bucket_counts.get(b, 0) + 1
            if b not in bucket_examples:
                bucket_examples[b] = []
            if len(bucket_examples[b]) < 2:
                bucket_examples[b].append(
                    {"id": ex_id, "input": row["input"], "raw_output": raw_output, "parsed": parsed_obj, "gold": gold_obj}
                )
            idx += 1
            continue

        tool_correct_count += 1

        if gold_tool == "create_support_ticket":
            create_total += 1
            gold_args = gold_obj.get("arguments", {})
            pred_args = parsed_obj.get("arguments", {})

            if pred_args.get("product", None) == gold_args.get("product", None):
                product_correct += 1
            if pred_args.get("category", None) == gold_args.get("category", None):
                category_correct += 1
            if pred_args.get("severity", None) == gold_args.get("severity", None):
                severity_correct += 1

        if gold_tool == "NEED_INFO":
            need_total += 1
            gold_args = gold_obj.get("arguments", {})
            pred_args = parsed_obj.get("arguments", {})

            gold_missing = gold_args.get("missing", [])
            pred_missing = pred_args.get("missing", [])

            gold_set = set(gold_missing)
            pred_set = set(pred_missing)

            if gold_set == pred_set:
                missing_set_correct += 1
            else:
                b = "NEED_INFO_WRONG_MISSING_SET"
                bucket_counts[b] = bucket_counts.get(b, 0) + 1
                if b not in bucket_examples:
                    bucket_examples[b] = []
                if len(bucket_examples[b]) < 2:
                    bucket_examples[b].append(
                        {"id": ex_id, "input": row["input"], "raw_output": raw_output, "parsed": parsed_obj, "gold": gold_obj}
                    )

        idx += 1

    def safe_rate(num, den):
        if den == 0:
            return None
        return float(num) / float(den)

    metrics = {}
    metrics["total_examples"] = total
    metrics["strict_json_pass_count"] = strict_json_pass
    metrics["schema_valid_pass_count"] = schema_valid_pass
    metrics["tool_correct_count"] = tool_correct_count

    metrics["strict_json_rate"] = safe_rate(strict_json_pass, total)
    metrics["schema_valid_rate"] = safe_rate(schema_valid_pass, total)
    metrics["tool_name_accuracy_on_schema_valid"] = safe_rate(tool_correct_count, schema_valid_pass)

    metrics["create_support_ticket_count_scored"] = create_total
    metrics["product_accuracy"] = safe_rate(product_correct, create_total)
    metrics["category_accuracy"] = safe_rate(category_correct, create_total)
    metrics["severity_accuracy"] = safe_rate(severity_correct, create_total)

    metrics["need_info_count_scored"] = need_total
    metrics["missing_set_accuracy"] = safe_rate(missing_set_correct, need_total)

    metrics["error_bucket_counts"] = bucket_counts

    write_json(metrics_out, metrics)

    # lora_error_buckets.md
    lines = []
    lines.append("# Baseline Error Buckets\n")
    lines.append("\n")
    lines.append("This file groups baseline failures by the first point of failure in the production-style pipeline.\n")
    lines.append("\n")
    lines.append("## Bucket counts\n")
    lines.append("\n")

    keys = list(bucket_counts.keys())
    keys.sort()
    i = 0
    while i < len(keys):
        k = keys[i]
        lines.append("- " + k + ": " + str(bucket_counts[k]) + "\n")
        i += 1

    lines.append("\n")
    lines.append("## Example failures (up to 2 per bucket)\n")
    lines.append("\n")

    i = 0
    while i < len(keys):
        k = keys[i]
        lines.append("### " + k + "\n")
        exs = bucket_examples.get(k, [])
        j = 0
        while j < len(exs):
            ex = exs[j]
            lines.append("- id: " + str(ex.get("id")) + "\n")
            lines.append("  - input: " + str(ex.get("input")) + "\n")
            lines.append("  - raw_output: " + str(ex.get("raw_output")).replace("\n", "\\n") + "\n")
            j += 1
        lines.append("\n")
        i += 1

    write_text(buckets_out, "".join(lines))

    print("WROTE:", metrics_out)
    print("WROTE:", buckets_out)


if __name__ == "__main__":
    main()
