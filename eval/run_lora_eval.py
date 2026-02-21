import json
import os
import time
import torch

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


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
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(tokenizer, system_text, user_text):
    messages = []
    messages.append({"role": "system", "content": system_text})
    messages.append({"role": "user", "content": user_text})

    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    s = ""
    s += system_text.strip()
    s += "\n\n"
    s += "User: " + user_text.strip() + "\n"
    s += "Assistant:"
    return s


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(repo_root, "runs", "lora_eval", "config.json")
    cfg = json.load(open(cfg_path, "r", encoding="utf-8"))

    base_model_id = cfg["base_model_id"]
    adapter_dir = os.path.join(repo_root, cfg["adapter_dir"])
    prompt_path = os.path.join(repo_root, cfg["prompt_path"])
    eval_path = os.path.join(repo_root, cfg["eval_path"])

    max_new_tokens = int(cfg["max_new_tokens"])
    do_sample = bool(cfg["do_sample"])
    temperature = float(cfg["temperature"])
    top_p = float(cfg["top_p"])
    seed = int(cfg["seed"])
    trust_remote_code = bool(cfg.get("trust_remote_code", False))

    torch.manual_seed(seed)

    system_text = load_text(prompt_path)
    gold_rows = read_jsonl(eval_path)

    use_cuda = torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=trust_remote_code)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs = {}
    if use_cuda:
        model_kwargs["device_map"] = "auto"
        model_kwargs["torch_dtype"] = "auto"
    else:
        model_kwargs["device_map"] = None
        model_kwargs["torch_dtype"] = torch.float32

    base_model = AutoModelForCausalLM.from_pretrained(base_model_id, trust_remote_code=trust_remote_code, **model_kwargs)
    if not use_cuda:
        base_model.to(device)

    model = PeftModel.from_pretrained(base_model, adapter_dir)
    model.eval()

    preds = []
    for ex in gold_rows:
        ex_id = ex["id"]
        user_input = ex["input"]
        gold_obj = ex.get("gold", {})

        prompt = build_prompt(tokenizer, system_text, user_input)
        inputs = tokenizer(prompt, return_tensors="pt")
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
        row["base_model_id"] = base_model_id
        row["adapter_dir"] = cfg["adapter_dir"]
        row["gen"] = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed
        }

        preds.append(row)

    out_path = os.path.join(repo_root, "eval", "lora_predictions.jsonl")
    write_jsonl(out_path, preds)
    print("WROTE:", out_path)
    print("N =", len(preds))
    print("DEVICE =", device)


if __name__ == "__main__":
    main()
