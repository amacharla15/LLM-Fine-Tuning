import json
from collections import Counter
from jsonschema import Draft7Validator

def read_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            rows.append(json.loads(s))
    return rows

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    train = read_jsonl("data/train.jsonl")
    val = read_jsonl("data/val.jsonl")
    test = read_jsonl("data/test.jsonl")
    all_rows = train + val + test

    schema_create = load_json("schemas/create_support_ticket.schema.json")
    schema_need = load_json("schemas/need_info.schema.json")
    v_create = Draft7Validator(schema_create)
    v_need = Draft7Validator(schema_need)

    tool_counts = Counter()
    schema_ok = 0
    schema_fail = 0
    enum_counts = Counter()

    for r in all_rows:
        out = r["output"]
        tool = out.get("tool_name")
        tool_counts[tool] += 1

        ok = (len(list(v_create.iter_errors(out))) == 0) or (len(list(v_need.iter_errors(out))) == 0)
        if ok:
            schema_ok += 1
        else:
            schema_fail += 1

        if tool == "create_support_ticket":
            args = out.get("arguments", {})
            enum_counts["product:"+str(args.get("product"))] += 1
            enum_counts["category:"+str(args.get("category"))] += 1
            enum_counts["severity:"+str(args.get("severity"))] += 1
            if "os" in args:
                enum_counts["os:"+str(args.get("os"))] += 1

    print("TOTAL =", len(all_rows))
    print("SCHEMA_OK =", schema_ok, "SCHEMA_FAIL =", schema_fail)
    print("TOOLS =", dict(tool_counts))
    print("TOP ENUMS:")
    for k, v in enum_counts.most_common(15):
        print(" ", k, "=", v)

if __name__ == "__main__":
    main()
