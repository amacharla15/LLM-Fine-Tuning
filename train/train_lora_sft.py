import json
import os
import random
import torch

from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def to_json_compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def build_text(tokenizer, system_text, user_text, assistant_obj):
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": to_json_compact(assistant_obj)},
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    s = ""
    s += system_text.strip() + "\n\n"
    s += "User: " + user_text.strip() + "\n"
    s += "Assistant: " + to_json_compact(assistant_obj)
    return s


def maybe_subset(ds, n):
    if n is None:
        return ds
    n = int(n)
    if n <= 0:
        return ds.select([])
    if n >= len(ds):
        return ds
    return ds.select(list(range(n)))


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(repo_root, "runs", "lora_sft", "config.json")
    cfg = json.load(open(cfg_path, "r", encoding="utf-8"))

    run_name = cfg["run_name"]
    base_model_id = cfg["base_model_id"]
    train_path = os.path.join(repo_root, cfg["train_path"])
    val_path = os.path.join(repo_root, cfg["val_path"])
    prompt_path = os.path.join(repo_root, cfg["prompt_path"])
    output_dir = os.path.join(repo_root, cfg["output_dir"])
    adapter_dir = os.path.join(repo_root, cfg["adapter_dir"])

    max_length = int(cfg["max_length"])
    num_train_epochs = float(cfg["num_train_epochs"])
    per_device_train_batch_size = int(cfg["per_device_train_batch_size"])
    per_device_eval_batch_size = int(cfg["per_device_eval_batch_size"])
    gradient_accumulation_steps = int(cfg["gradient_accumulation_steps"])
    learning_rate = float(cfg["learning_rate"])
    logging_steps = int(cfg["logging_steps"])
    save_strategy = cfg["save_strategy"]
    eval_strategy = cfg["eval_strategy"]

    lora_r = int(cfg["lora_r"])
    lora_alpha = int(cfg["lora_alpha"])
    lora_dropout = float(cfg["lora_dropout"])
    target_modules = cfg["target_modules"]

    seed = int(cfg["seed"])

    torch.manual_seed(seed)
    random.seed(seed)

    system_text = load_text(prompt_path)

    tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    use_cuda = torch.cuda.is_available()
    model_kwargs = {}
    if use_cuda:
        model_kwargs["device_map"] = "auto"
        model_kwargs["torch_dtype"] = "auto"
    else:
        model_kwargs["device_map"] = None

    model = AutoModelForCausalLM.from_pretrained(base_model_id, trust_remote_code=True, **model_kwargs)
    if not use_cuda:
        model.to("cpu")

    model.config.use_cache = False

    data_files = {"train": train_path, "validation": val_path}
    ds = load_dataset("json", data_files=data_files)

    n_train_subset = os.environ.get("N_TRAIN_SUBSET", "").strip()
    n_val_subset = os.environ.get("N_VAL_SUBSET", "").strip()

    train_ds = ds["train"]
    val_ds = ds["validation"]

    if n_train_subset != "":
        train_ds = maybe_subset(train_ds, int(n_train_subset))
    if n_val_subset != "":
        val_ds = maybe_subset(val_ds, int(n_val_subset))

    def map_row(row):
        t = build_text(tokenizer, system_text, row["input"], row["output"])
        return {"text": t}

    train_ds = train_ds.map(map_row, remove_columns=train_ds.column_names)
    val_ds = val_ds.map(map_row, remove_columns=val_ds.column_names)

    lora_cfg = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=target_modules,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_cfg)

    args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_eval_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        logging_steps=logging_steps,
        save_strategy=save_strategy,
        eval_strategy=eval_strategy,
        save_total_limit=2,
        seed=seed,
        report_to=[],
        fp16=False,
        bf16=False,
        dataset_text_field="text",
        max_length=max_length,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
    )

    print("RUN_NAME =", run_name)
    print("BASE_MODEL =", base_model_id)
    print("DEVICE =", "cuda" if use_cuda else "cpu")
    print("TRAIN_N =", len(train_ds))
    print("VAL_N =", len(val_ds))

    trainer.train()

    os.makedirs(adapter_dir, exist_ok=True)
    trainer.model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)

    print("SAVED_ADAPTER =", adapter_dir)


if __name__ == "__main__":
    main()