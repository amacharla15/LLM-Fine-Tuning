import json
import os
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def read_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s == "":
                continue
            rows.append(json.loads(s))
    return rows


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        i = 0
        while i < len(rows):
            f.write(json.dumps(rows[i], ensure_ascii=False) + "\n")
            i += 1


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(tokenizer, system_text, user_text):
    messages = []
    messages.append({"role": "system", "content": system_text})
    messages.append({"role": "user", "content": user_text})

    if hasattr(tokenizer, "apply_chat_template"):
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        return prompt

    prompt = ""
    prompt += system_text.strip()
    prompt += "\n\n"
    prompt += "User: " + user_text.strip() + "\n"
    prompt += "Assistant:"
    return prompt


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    gold_path = os.path.join(repo_root, "eval", "10_gold_examples.jsonl")
    prompt_path = os.path.join(repo_root, "eval", "prompt_template.txt")
    cfg_path = os.path.join(repo_root, "runs", "baseline", "config.json")
    out_path = os.path.join(repo_root, "eval", "baseline_predictions.jsonl")

    gold_rows = read_jsonl(gold_path)
    system_text = load_text(prompt_path)

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    model_id = cfg["model_id"]
    max_new_tokens = int(cfg["max_new_tokens"])
    do_sample = bool(cfg["do_sample"])
    temperature = float(cfg["temperature"])
    top_p = float(cfg["top_p"])
    seed = int(cfg["seed"])
    trust_remote_code = bool(cfg.get("trust_remote_code", False))

    torch.manual_seed(seed)

    use_cuda = torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=trust_remote_code)

    model_kwargs = {}
    if use_cuda:
        model_kwargs["device_map"] = "auto"
        model_kwargs["torch_dtype"] = "auto"
    else:
        model_kwargs["device_map"] = None

    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=trust_remote_code, **model_kwargs)

    if not use_cuda:
        model.to(device)

    model.eval()

    predictions = []
    idx = 0
    while idx < len(gold_rows):
        ex = gold_rows[idx]
        ex_id = ex["id"]
        user_input = ex["input"]
        gold_obj = ex.get("gold", {})

        prompt = build_prompt(tokenizer, system_text, user_input)

        inputs = tokenizer(prompt, return_tensors="pt")
        if not use_cuda:
            inputs = {k: v.to(device) for (k, v) in inputs.items()}

        t0 = time.time()
        with torch.no_grad():
            out_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=do_sample,
                temperature=temperature if do_sample else None,
                top_p=top_p if do_sample else None
            )
        t1 = time.time()

        gen_ids = out_ids[0][inputs["input_ids"].shape[1]:]
        raw_output = tokenizer.decode(gen_ids, skip_special_tokens=True)

        row = {}
        row["id"] = ex_id
        row["input"] = user_input
        row["gold_tool_name"] = gold_obj.get("tool_name", None)
        row["raw_output"] = raw_output
        row["latency_sec"] = float(t1 - t0)
        row["model_id"] = model_id
        row["gen"] = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed
        }

        predictions.append(row)
        idx += 1

    write_jsonl(out_path, predictions)
    print("WROTE:", out_path)
    print("N =", len(predictions))
    print("DEVICE =", device)
    print("MODEL =", model_id)


if __name__ == "__main__":
    main()
