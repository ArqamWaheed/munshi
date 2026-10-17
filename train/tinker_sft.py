"""LoRA SFT of the parser on Tinker with the RAW SDK (tinker 0.33.1). No tinker-cookbook, so no torch.

Data: data/train.jsonl rows {today, message, label}. The prompt is SHORT_PROMPT + "TODAY/MESSAGE";
the target is the canonical label JSON. Loss only on the assistant tokens (weights 0 on the prompt).
Chat template: Qwen3.5/Qwen3 HF template with enable_thinking=False (renders an empty <think></think>),
identical to munshi.llm.render_prompt used at serving time.

Defaults for ~900 examples: rank 32, LR 5e-4 (cookbook get_lr formula for Qwen ~4.9e-4 at hidden 2560),
batch 32, 3 epochs (~85 steps), linear decay. Est. cost: 900 x ~250 tok x 3 ep ~= 0.7M train tok
~= $0.50 on Qwen3.5-4B. Prints the console URL, loss curve file, and the tinker:// sampler path.

  python -m train.tinker_sft --epochs 3
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
from datetime import date
from pathlib import Path

import tinker

from munshi import config as cfg
from munshi.parser import SHORT_PROMPT, apply_rules, label_to_target, normalise, user_turn

ROOT = Path(__file__).resolve().parent.parent


def load_rows(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


# "28 Oct", "Nov 5", "15th", "25 ko": the generator draws a random TODAY, so an explicit date can land in the
# past and normalise() nulls it. Those rows teach "drop the date"; they are excluded (6 of the first 732).
_MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
EXPLICIT_DATE = re.compile(rf"\b\d{{1,2}}\s*(st|nd|rd|th)?\s*{_MON}\b|\b{_MON}\s*\d{{1,2}}\b|"
                           r"\b\d{1,2}\s*(tareekh|tarikh|ko)\b|\b\d{1,2}(st|nd|rd|th)\b", re.I)


def select_rows(rows: list[dict], max_clar_frac: float, seed: int = 0) -> tuple[list[dict], dict]:
    """Drop past-date artefacts, then cap rows needing clarification at max_clar_frac of the set. The eval set
    is ~19% clarification; the teacher's data came out ~60%, which biases the parser towards "unknown"."""
    labelled = [(r, normalise(r["label"], date.fromisoformat(r["today"]))) for r in rows]
    kept = [(r, inq) for r, inq in labelled if not (inq.check_in is None and EXPLICIT_DATE.search(r["message"]))]
    clar = [r for r, inq in kept if inq.needs_clarification]
    full = [r for r, inq in kept if not inq.needs_clarification]
    cap = int(max_clar_frac * len(full) / (1 - max_clar_frac)) if max_clar_frac < 1 else len(clar)
    clar = random.Random(seed).sample(clar, min(cap, len(clar)))
    stats = {"input": len(rows), "past_date_artefacts": len(labelled) - len(kept), "complete": len(full),
             "clarification_kept": len(clar), "clarification_dropped": sum(1 for _, i in kept if i.needs_clarification) - len(clar)}
    return full + clar, stats


def to_messages(row: dict) -> tuple[list[dict], str]:
    today = date.fromisoformat(row["today"])
    target = label_to_target(apply_rules(row["label"], row["message"], today))
    return ([{"role": "system", "content": SHORT_PROMPT},
             {"role": "user", "content": user_turn(row["message"], today)}], target)


def make_datum(tokenizer, prompt_msgs: list[dict], target: str) -> tinker.Datum:
    prompt_text = tokenizer.apply_chat_template(prompt_msgs, tokenize=False, add_generation_prompt=True,
                                                enable_thinking=False)
    full_text = tokenizer.apply_chat_template(prompt_msgs + [{"role": "assistant", "content": target}],
                                              tokenize=False, enable_thinking=False)
    assert full_text.startswith(prompt_text), "chat template is not prefix-consistent"
    p_tok = tokenizer.encode(prompt_text, add_special_tokens=False)
    c_tok = tokenizer.encode(full_text[len(prompt_text):], add_special_tokens=False)  # target + <|im_end|>\n
    tokens, weights = p_tok + c_tok, [0.0] * len(p_tok) + [1.0] * len(c_tok)
    return tinker.Datum(model_input=tinker.ModelInput.from_ints(tokens[:-1]),
                        loss_fn_inputs={"target_tokens": tokens[1:], "weights": weights[1:]})


def batch_loss(fb, batch: list[tinker.Datum]) -> float:
    lp = [x for out in fb.loss_fn_outputs for x in out["logprobs"].tolist()]
    w = [x for d in batch for x in d.loss_fn_inputs["weights"].tolist()]
    return -sum(a * b for a, b in zip(lp, w)) / max(sum(w), 1.0)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", default=cfg.TINKER_BASE_MODEL)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--name", default="munshi-parser")
    ap.add_argument("--max-clar-frac", type=float, default=0.3)
    a = ap.parse_args()

    service = tinker.ServiceClient()  # reads TINKER_API_KEY
    trainer = await service.create_lora_training_client_async(base_model=a.base_model, rank=a.rank, seed=0)
    tok = trainer.get_tokenizer()
    rows, selection = select_rows(load_rows(ROOT / "data" / "train.jsonl"), a.max_clar_frac)
    print("training rows:", selection)
    train = [make_datum(tok, *to_messages(r)) for r in rows]
    dev_path = ROOT / "data" / "dev.jsonl"
    dev = [make_datum(tok, *to_messages(r)) for r in load_rows(dev_path)][:64] if dev_path.exists() else []
    n_tok = sum(d.model_input.length for d in train)
    print(f"{len(train)} examples, {n_tok} tokens/epoch; console: {service.get_console_url()}")

    steps_per_epoch = max(1, len(train) // a.batch)
    total, step, log = steps_per_epoch * a.epochs, 0, []
    rng = random.Random(0)
    for epoch in range(a.epochs):
        rng.shuffle(train)
        for i in range(steps_per_epoch):
            batch = train[i * a.batch:(i + 1) * a.batch]
            lr = a.lr * (1 - step / total)  # linear decay
            fb_fut = await trainer.forward_backward_async(batch, "cross_entropy")
            opt_fut = await trainer.optim_step_async(tinker.AdamParams(learning_rate=lr))
            fb = await fb_fut.result_async()
            await opt_fut.result_async()
            entry = {"step": step, "epoch": epoch, "lr": lr, "train_nll": batch_loss(fb, batch)}
            if dev and (step % 10 == 0 or step == total - 1):
                dfb = await (await trainer.forward_async(dev, "cross_entropy")).result_async()
                entry["dev_nll"] = batch_loss(dfb, dev)
            log.append(entry)
            print(json.dumps(entry))
            step += 1

    ckpt = await (await trainer.save_weights_for_sampler_async(name=a.name)).result_async()
    out = ROOT / "results" / ("train_log.json" if a.name == "munshi-parser" else f"train_log_{a.name}.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"base_model": a.base_model, "rank": a.rank, "lr": a.lr, "batch": a.batch,
                               "epochs": a.epochs, "examples": len(train), "train_tokens_per_epoch": n_tok,
                               "selection": selection,
                               "sampler_path": ckpt.path, "log": log}, indent=2))
    print(f"\nSAMPLER PATH (put in .env as TINKER_MODEL_PATH):\n{ckpt.path}")
    print(f"playground: {ckpt.get_playground_url()}\nloss log: {out}")


if __name__ == "__main__":
    asyncio.run(main())
