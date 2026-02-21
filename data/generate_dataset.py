import json
import os
import random
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRODUCTS = ["vpn","email","laptop","account","network","printer","app"]
CATEGORIES = ["access","bug","performance","outage","request","billing"]
SEVERITIES = ["low","medium","high","critical"]
OS_LIST = ["windows","macos","linux","ios","android","unknown"]

def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def maybe_email(rng):
    # only valid emails; otherwise omit entirely
    if rng.random() < 0.15:
        user = rng.choice(["alex","sam","jordan","taylor","casey","priya","chen"])
        dom = rng.choice(["example.com","corp.com","school.edu"])
        return user + "@" + dom
    return None

def add_noise(rng, s):
    # mild realistic noise
    if rng.random() < 0.2:
        s = s.replace(".", "!")
    if rng.random() < 0.15:
        s = s + " " + rng.choice(["ASAP.", "urgent.", "pls help.", "thx."])
    if rng.random() < 0.10:
        s = s.upper()
    return s

def mk_create(product, category, severity, summary, description, os_val=None, email=None):
    args = {
        "product": product,
        "category": category,
        "severity": severity,
        "summary": summary,
        "description": description
    }
    if os_val is not None:
        args["os"] = os_val
    if email is not None:
        args["user_email"] = email
    return {"tool_name":"create_support_ticket","arguments":args}

def mk_need(missing):
    return {"tool_name":"NEED_INFO","arguments":{"missing":missing}}

def gen_examples(rng, n_total):
    rows = []


    templates = []

    templates.append(("create", lambda: (
        add_noise(rng, rng.choice([
            "Office internet is down for multiple people. No one can load any websites right now.",
            "WiFi is down across the floor. No sites load.",
            "Network outage: can't reach any external websites.",
            "LAN is down. Everyone is offline."
        ])),
        mk_create(
            "network","outage",rng.choice(["high","critical"]),
            "Network outage affecting multiple users",
            "Multiple users report no website access / connectivity. Investigate network outage.",
            os_val="unknown",
            email=maybe_email(rng)
        )
    )))

    # PASSWORD RESET / LOGIN -> category access (NOT "password")
    templates.append(("create", lambda: (
        add_noise(rng, rng.choice([
            "I can’t reset my password. The reset link says it’s expired immediately.",
            "Password reset link expires instantly every time.",
            "Login reset email link is invalid right away."
        ])),
        mk_create(
            "account","access",rng.choice(["medium","high"]),
            "Password reset link expires immediately",
            "User cannot reset password; reset link appears expired immediately after generation.",
            os_val="unknown",
            email=maybe_email(rng)
        )
    )))

    # VPN DISCONNECTS -> vpn + performance
    templates.append(("create", lambda: (
        add_noise(rng, rng.choice([
            "VPN disconnects every 5 minutes on my Mac. I can't work.",
            "VPN keeps dropping on macOS since this morning.",
            "My VPN disconnects repeatedly and interrupts work."
        ])),
        mk_create(
            "vpn","performance",rng.choice(["high","critical"]),
            "VPN disconnects repeatedly on macOS",
            "User reports VPN drops frequently (about every few minutes). Needs investigation.",
            os_val="macos",
            email=maybe_email(rng)
        )
    )))

    # EMAIL NOT SYNCING ON IPHONE -> email + performance + os ios
    templates.append(("create", lambda: (
        add_noise(rng, rng.choice([
            "Email is not syncing on my iPhone since yesterday. No new messages are coming in.",
            "My iPhone mail stopped syncing. Inbox doesn't update.",
            "Email isn't updating on iOS since yesterday."
        ])),
        mk_create(
            "email","performance",rng.choice(["medium","high"]),
            "Email not syncing on iOS",
            "User reports email does not sync / no new messages since yesterday on iPhone.",
            os_val="ios",
            email=maybe_email(rng)
        )
    )))

    # APP CRASHING BUT APP UNKNOWN -> NEED_INFO product
    templates.append(("need", lambda: (
        add_noise(rng, rng.choice([
            "It keeps crashing every time I open it. Please fix ASAP.",
            "This thing crashes whenever I launch it.",
            "Crashes on open. Need help."
        ])),
        mk_need(["product"])
    )))

    # ACCESS DENIED BUT PRODUCT UNCLEAR -> NEED_INFO product
    templates.append(("need", lambda: (
        add_noise(rng, rng.choice([
            "I can't log in. Access denied.",
            "Access denied when I try to sign in.",
            "Login fails with access denied."
        ])),
        mk_need(["product"])
    )))

    # PRINTER JAM / NOT PRINTING -> printer + outage or bug
    templates.append(("create", lambda: (
        add_noise(rng, rng.choice([
            "Printer won't print and shows a paper jam error even after clearing.",
            "Office printer stopped printing; keeps saying paper jam.",
            "Printer is stuck and printing fails."
        ])),
        mk_create(
            "printer",rng.choice(["outage","bug"]),rng.choice(["medium","high"]),
            "Printer not printing; paper jam error persists",
            "Printer reports paper jam and refuses to print even after clearing. Needs troubleshooting.",
            os_val="unknown",
            email=maybe_email(rng)
        )
    )))

    # BILLING CHARGE -> billing + request
    templates.append(("create", lambda: (
        add_noise(rng, rng.choice([
            "I was charged twice this month. Please check my billing.",
            "Billing issue: duplicate charge on my account.",
            "I think I got overbilled."
        ])),
        mk_create(
            "account","billing",rng.choice(["low","medium"]),
            "Possible duplicate billing charge",
            "User reports duplicate/incorrect charge and requests billing review.",
            os_val="unknown",
            email=maybe_email(rng)
        )
    )))

    # Generate
    i = 0
    while i < n_total:
        kind, fn = rng.choice(templates)
        inp, out = fn()

        row = {
            "id": "ex_%06d" % i,
            "input": inp,
            "output": out
        }
        rows.append(row)
        i += 1

    return rows

def split(rows, rng):
    rng.shuffle(rows)
    n = len(rows)
    n_train = int(0.8 * n)
    n_val = int(0.1 * n)
    train = rows[:n_train]
    val = rows[n_train:n_train+n_val]
    test = rows[n_train+n_val:]
    return train, val, test

def main():
    rng = random.Random(42)


    n_total = int(os.environ.get("N_EXAMPLES", "800"))

    rows = gen_examples(rng, n_total)
    train, val, test = split(rows, rng)

    out_dir = os.path.join(REPO_ROOT, "data")
    write_jsonl(os.path.join(out_dir, "train.jsonl"), train)
    write_jsonl(os.path.join(out_dir, "val.jsonl"), val)
    write_jsonl(os.path.join(out_dir, "test.jsonl"), test)

    print("WROTE data/train.jsonl =", len(train))
    print("WROTE data/val.jsonl   =", len(val))
    print("WROTE data/test.jsonl  =", len(test))
    print("TIP: set N_EXAMPLES=2000 for bigger dataset")

if __name__ == "__main__":
    main()
