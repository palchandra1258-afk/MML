#!/usr/bin/env python3
"""Train temporal knowledge-tracing models on the existing EdNet KT1 split.

The models predict a later submitted-answer correctness label from prior
question/answer interactions. The test partition is deliberately never read as
an input target or evaluated. Training is restricted to the Phase 6 5% learner
sample, and validation learners are split into early-stop, calibration, and
report-only groups.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import random
import resource
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import torch
from scipy.optimize import minimize_scalar
from scipy.special import expit, logit
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset
import xgboost as xgb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from mcp_ri.models.ednet_logistic import (  # noqa: E402
    SparseFeatureEncoder,
    row_is_training_sample,
    classification_metrics,
    assert_training_feature_whitelist,
)


@dataclass
class SequenceRecord:
    questions: np.ndarray
    answers: np.ndarray
    role: int = -1  # 0=early stop, 1=calibration, 2=report-only
    offset: int = -1


class WindowDataset(Dataset):
    def __init__(self, records: list[SequenceRecord], max_length: int = 200,
                 role: int | None = None):
        self.records = records
        self.windows: list[tuple[int, int, int]] = []
        stride = max_length - 1
        for sequence_i, record in enumerate(records):
            if role is not None and record.role != role:
                continue
            n = len(record.questions)
            start = 0
            while start < n - 1:
                end = min(start + max_length, n)
                if end - start >= 2:
                    self.windows.append((sequence_i, start, end))
                if end == n:
                    break
                start += stride

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, index):
        sequence_i, start, end = self.windows[index]
        record = self.records[sequence_i]
        return (record.questions[start:end], record.answers[start:end],
                sequence_i, start, end)


def collate_windows(batch):
    max_len = max(len(item[0]) for item in batch)
    questions = torch.zeros((len(batch), max_len), dtype=torch.long)
    answers = torch.zeros((len(batch), max_len), dtype=torch.long)
    lengths = torch.empty(len(batch), dtype=torch.long)
    meta = []
    for i, (q, y, sequence_i, start, end) in enumerate(batch):
        n = len(q)
        questions[i, :n] = torch.from_numpy(q.astype(np.int64, copy=False))
        answers[i, :n] = torch.from_numpy(y.astype(np.int64, copy=False))
        lengths[i] = n
        meta.append((sequence_i, start, end))
    return questions, answers, lengths, meta


class DKT(nn.Module):
    """Deep Knowledge Tracing: LSTM interactions -> next-item response logits."""
    def __init__(self, n_items: int, dim: int = 128, layers: int = 1, dropout: float = 0.2):
        super().__init__()
        self.interaction = nn.Embedding(n_items * 2, dim)
        self.lstm = nn.LSTM(dim, dim, num_layers=layers, batch_first=True,
                            dropout=dropout if layers > 1 else 0.0)
        self.dropout = nn.Dropout(dropout)
        self.output = nn.Linear(dim, n_items)

    def forward(self, q, y, target_q, lengths):
        x = self.interaction(q * 2 + y)
        h, _ = self.lstm(x)
        logits = self.output(self.dropout(h))
        return logits.gather(-1, target_q.unsqueeze(-1)).squeeze(-1)


class SAKTStyle(nn.Module):
    """Causal question-query / prior-response attention sequence model."""
    def __init__(self, n_items: int, dim: int = 128, heads: int = 4,
                 max_length: int = 200, dropout: float = 0.2):
        super().__init__()
        self.interaction = nn.Embedding(n_items * 2, dim)
        self.question = nn.Embedding(n_items, dim)
        self.position = nn.Embedding(max_length, dim)
        self.attention = nn.MultiheadAttention(dim, heads, dropout=dropout,
                                              batch_first=True)
        self.norm1 = nn.LayerNorm(dim)
        self.ff = nn.Sequential(nn.Linear(dim, dim * 4), nn.GELU(),
                                nn.Dropout(dropout), nn.Linear(dim * 4, dim))
        self.norm2 = nn.LayerNorm(dim)
        self.dropout = nn.Dropout(dropout)
        self.output = nn.Linear(dim, 1)

    def forward(self, q, y, target_q, lengths):
        # q/y are the observed interactions; target_q is the following item.
        steps = target_q.shape[1]
        idx = torch.arange(steps, device=q.device).unsqueeze(0)
        valid_keys = idx < (lengths - 1).unsqueeze(1)
        key_padding = ~valid_keys
        query = self.question(target_q) + self.position(idx)
        key_value = self.interaction(q * 2 + y)
        causal = torch.triu(torch.ones((steps, steps), dtype=torch.bool,
                                       device=q.device), diagonal=1)
        attended, _ = self.attention(query, key_value, key_value,
                                     attn_mask=causal,
                                     key_padding_mask=key_padding,
                                     need_weights=False)
        h = self.norm1(query + self.dropout(attended))
        h = self.norm2(h + self.dropout(self.ff(h)))
        return self.output(h).squeeze(-1)


def learner_role(learner_id: str, seed: int) -> int:
    digest = hashlib.blake2b(f"phase8:{seed}:{learner_id}".encode(),
                             digest_size=8, person=b"mcp-ri-role").digest()
    bucket = int.from_bytes(digest, "big") % 10
    return 0 if bucket == 0 else (1 if bucket == 1 else 2)


def _flush_prediction_rows(rows: list[dict[str, str]], encoder, models,
                           prevalence: float, output: dict[str, list[np.ndarray]],
                           targets: list[np.ndarray], learner_counts: Counter):
    if not rows:
        return
    y = np.fromiter((int(r["correctness"]) for r in rows), dtype=np.int8,
                    count=len(rows))
    x, _ = encoder.transform(rows)
    probs = {
        "majority": np.full(len(y), prevalence, dtype=np.float32),
        "last_response": np.fromiter(
            (float(r["previous_response_correctness"])
             if r.get("previous_response_correctness", "") else prevalence
             for r in rows), dtype=np.float32, count=len(rows)),
        "historical_accuracy": np.fromiter(
            (float(r["prior_accuracy"]) if r.get("prior_accuracy", "") else prevalence
             for r in rows), dtype=np.float32, count=len(rows)),
        "sgd_logistic": models["sgd_logistic"].predict_proba(x)[:, 1].astype(np.float32),
        "random_forest": models["random_forest"].predict_proba(x)[:, 1].astype(np.float32),
        "xgboost_600": models["xgboost_600"].predict_proba(x)[:, 1].astype(np.float32),
    }
    for name, value in probs.items():
        output[name].append(value)
    targets.append(y)
    learner_counts["validation_targets_scored_for_existing_models"] += len(y)
    rows.clear()


def load_sequences(dataset: Path, encoder: SparseFeatureEncoder, models,
                   prevalence: float, seed: int, batch_size: int):
    """One ordered scan. Test rows are only skipped; their target is never read."""
    train_records: list[SequenceRecord] = []
    val_records: list[SequenceRecord] = []
    val_predictions: dict[str, list[np.ndarray]] = {
        k: [] for k in ("majority", "last_response", "historical_accuracy",
                        "sgd_logistic", "random_forest", "xgboost_600")}
    scored_target_chunks: list[np.ndarray] = []
    val_role_chunks: list[np.ndarray] = []
    val_group_chunks: list[np.ndarray] = []
    raw_val_batch: list[dict[str, str]] = []
    counts = Counter()
    q_index = encoder.question_index
    unknown_q = len(q_index)
    current_id = None
    current_split = None
    current_train_selected = False
    current_train_selection_decided = False
    current_role = -1
    current_q: list[int] = []
    current_y: list[int] = []
    val_offset = 0
    next_group_id = 0
    last_source_learner = None
    closed_source_learners: set[str] = set()

    def finish_learner():
        nonlocal current_q, current_y, val_offset, next_group_id
        if current_id is None or not current_q:
            current_q, current_y = [], []
            return
        rec = SequenceRecord(np.asarray(current_q, dtype=np.uint16),
                             np.asarray(current_y, dtype=np.int8))
        if current_split == "train" and current_train_selected:
            train_records.append(rec)
            counts["train_learners"] += 1
            counts["train_target_interactions"] += len(current_q)
            counts["train_transitions"] += max(len(current_q) - 1, 0)
        elif current_split == "validation":
            rec.role = current_role
            rec.offset = val_offset
            val_records.append(rec)
            role_n = {0: "early_stop", 1: "calibration", 2: "report"}[current_role]
            counts[f"validation_{role_n}_learners"] += 1
            counts[f"validation_{role_n}_targets"] += len(current_q)
            val_role_chunks.append(np.full(len(current_q), current_role, dtype=np.uint8))
            val_group_chunks.append(np.full(len(current_q), next_group_id, dtype=np.int64))
            val_offset += len(current_q)
            next_group_id += 1
        current_q, current_y = [], []

    with gzip.open(dataset, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"learner_id", "correctness", "current_question_id", "split_unseen_learner"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"processed dataset lacks fields: {sorted(required-set(reader.fieldnames or []))}")
        for row in reader:
            counts["processed_rows_scanned"] += 1
            if counts["processed_rows_scanned"] % 10_000_000 == 0:
                print(f"Scanned {counts['processed_rows_scanned']:,} processed rows", flush=True)
            source_learner = row.get("learner_id", "")
            if source_learner != last_source_learner:
                if last_source_learner is not None:
                    closed_source_learners.add(last_source_learner)
                if source_learner in closed_source_learners:
                    raise ValueError("processed rows are not contiguous by learner; refusing to split sequence history")
                last_source_learner = source_learner
            split = row.get("split_unseen_learner", "")
            if split not in {"train", "validation"}:
                # Intentionally do not read correctness for test rows.
                continue
            learner_id = source_learner
            if learner_id != current_id:
                finish_learner()
                current_id = learner_id
                current_split = split
                current_train_selected = False
                current_train_selection_decided = False
                current_role = learner_role(learner_id, seed)
            if split == "train":
                counts["train_source_rows_seen"] += 1
            elif split == "validation":
                counts["validation_source_rows_seen"] += 1
            label = row.get("correctness", "")
            if label not in {"0", "1"}:
                counts["unlabelled_candidate_rows"] += 1
                continue
            if split == "train":
                if not current_train_selection_decided:
                    current_train_selected = row_is_training_sample(
                        row, seed=seed, sample_percent=5
                    )
                    current_train_selection_decided = True
                if not current_train_selected:
                    continue
            qid = row.get("current_question_id", "")
            qi = q_index.get(qid, unknown_q)
            if qi == unknown_q:
                counts[f"unknown_question_{split}"] += 1
            current_q.append(qi)
            current_y.append(int(label))
            if split == "validation":
                raw_val_batch.append(row)
                if len(raw_val_batch) >= batch_size:
                    before = counts["validation_targets_scored_for_existing_models"]
                    _flush_prediction_rows(raw_val_batch, encoder, models, prevalence,
                                           val_predictions, scored_target_chunks,
                                           counts)
                    # Role and group arrays are appended when learner groups close.
                    after = counts["validation_targets_scored_for_existing_models"]
                    if before // 1_000_000 != after // 1_000_000:
                        print(f"Prepared validation predictions: {after:,}", flush=True)
        finish_learner()
        _flush_prediction_rows(raw_val_batch, encoder, models, prevalence,
                               val_predictions, scored_target_chunks, counts)

    # Validate that streamed baseline scores align with learner-ordered sequences.
    val_y = np.concatenate([r.answers for r in val_records])
    role = np.concatenate(val_role_chunks)
    group = np.concatenate(val_group_chunks)
    old_model_y = np.concatenate(scored_target_chunks)
    if not np.array_equal(val_y, old_model_y):
        raise ValueError("streamed validation labels do not align with chronological sequences")
    predictions = {name: np.concatenate(chunks) for name, chunks in val_predictions.items()}
    if any(len(p) != len(val_y) for p in predictions.values()):
        raise ValueError("existing-model validation predictions are not row-aligned")
    if len(role) != len(val_y) or len(group) != len(val_y):
        raise ValueError("validation roles/groups are not aligned to target rows")
    for record in val_records:
        if len(record.questions) != len(record.answers):
            raise ValueError("question and response sequence lengths differ")
    return train_records, val_records, val_y, role, group, predictions, dict(counts)


def build_model(name: str, n_items: int, max_length: int):
    if name == "dkt":
        return DKT(n_items=n_items, dim=128, layers=1, dropout=0.2)
    if name == "sakt":
        return SAKTStyle(n_items=n_items, dim=128, heads=4,
                         max_length=max_length, dropout=0.2)
    raise ValueError(name)


def move_batch(batch, device):
    q, y, lengths, meta = batch
    return (q.to(device, non_blocking=True), y.to(device, non_blocking=True),
            lengths.to(device, non_blocking=True), meta)


def model_logits(model, model_name: str, q, y, lengths):
    q_in, y_in, q_target = q[:, :-1], y[:, :-1], q[:, 1:]
    return model(q_in, y_in, q_target, lengths)


def valid_mask(lengths, steps, device):
    return torch.arange(steps, device=device).unsqueeze(0) < (lengths - 1).unsqueeze(1)


@torch.no_grad()
def validation_loss(model, name: str, records: list[SequenceRecord], role: int,
                    batch_size: int, max_length: int, device: torch.device):
    dataset = WindowDataset(records, max_length, role=role)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False,
                        num_workers=0, collate_fn=collate_windows)
    model.eval()
    loss_sum = 0.0
    n = 0
    for batch in loader:
        q, y, lengths, _ = move_batch(batch, device)
        logits = model_logits(model, name, q, y, lengths)
        target = y[:, 1:].float()
        mask = valid_mask(lengths, logits.shape[1], device)
        loss = F.binary_cross_entropy_with_logits(logits.float(), target, reduction="none")
        loss_sum += float((loss * mask).sum().item())
        n += int(mask.sum().item())
    if n == 0:
        raise ValueError("early-stopping validation cohort contains no transitions")
    return loss_sum / n, n


def train_one_model(name: str, train_records: list[SequenceRecord], val_records: list[SequenceRecord],
                    n_items: int, device: torch.device, output_path: Path,
                    seed: int, max_epochs: int, batch_size: int, max_length: int,
                    patience: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.cuda.reset_peak_memory_stats()
    model = build_model(name, n_items, max_length).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)
    train_data = WindowDataset(train_records, max_length)
    generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True,
                              num_workers=0, collate_fn=collate_windows,
                              generator=generator, pin_memory=device.type == "cuda")
    best = math.inf
    best_epoch = 0
    bad_epochs = 0
    history = []
    started = time.monotonic()
    best_state = None
    for epoch in range(1, max_epochs + 1):
        model.train()
        epoch_start = time.monotonic()
        loss_total = 0.0
        targets_total = 0
        for batch in train_loader:
            q, y, lengths, _ = move_batch(batch, device)
            optimizer.zero_grad(set_to_none=True)
            logits = model_logits(model, name, q, y, lengths)
            target = y[:, 1:].float()
            mask = valid_mask(lengths, logits.shape[1], device)
            losses = F.binary_cross_entropy_with_logits(logits.float(), target, reduction="none")
            loss = (losses * mask).sum() / mask.sum().clamp_min(1)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            count = int(mask.sum().item())
            loss_total += float((losses.detach() * mask).sum().item())
            targets_total += count
        stop_loss, stop_n = validation_loss(model, name, val_records, role=0,
                                            batch_size=batch_size, max_length=max_length,
                                            device=device)
        item = {"epoch": epoch,
                "train_log_loss": loss_total / max(targets_total, 1),
                "early_stop_log_loss": stop_loss,
                "early_stop_examples": stop_n,
                "epoch_seconds": time.monotonic() - epoch_start}
        history.append(item)
        print(f"{name} epoch={epoch}/{max_epochs} train_loss={item['train_log_loss']:.6f} "
              f"stop_loss={stop_loss:.6f} seconds={item['epoch_seconds']:.1f}", flush=True)
        if stop_loss < best - 1e-5:
            best = stop_loss
            best_epoch = epoch
            bad_epochs = 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            torch.save({"model": name, "state_dict": best_state,
                        "config": {"n_items": n_items, "max_length": max_length,
                                   "dimension": 128, "seed": seed}}, output_path)
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                break
    if best_state is None:
        raise RuntimeError(f"no checkpoint selected for {name}")
    model.load_state_dict(best_state)
    model.to(device)
    total_seconds = time.monotonic() - started
    return model, {"best_epoch": best_epoch, "best_early_stop_log_loss": best,
                   "epochs_completed": len(history), "epoch_history": history,
                   "training_windows": len(train_data),
                   "training_transitions": sum(max(len(r.questions) - 1, 0) for r in train_records),
                   "fit_seconds": total_seconds,
                   "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0,
                   "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved() if torch.cuda.is_available() else 0,
                   "artifact": str(output_path)}


@torch.no_grad()
def predict_sequences(model, name: str, records: list[SequenceRecord], n_rows: int,
                      batch_size: int, max_length: int, device: torch.device):
    predictions = np.full(n_rows, np.nan, dtype=np.float32)
    dataset = WindowDataset(records, max_length)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False,
                        num_workers=0, collate_fn=collate_windows,
                        pin_memory=device.type == "cuda")
    model.eval()
    for batch in loader:
        q, y, lengths, meta = move_batch(batch, device)
        logits = model_logits(model, name, q, y, lengths)
        probabilities = torch.sigmoid(logits.float()).cpu().numpy()
        valid = (lengths - 1).cpu().numpy()
        for i, (sequence_i, start, end) in enumerate(meta):
            n = int(valid[i])
            record = records[sequence_i]
            # Output step j predicts this sequence's target at start+j+1.
            left = record.offset + start + 1
            right = record.offset + start + 1 + n
            predictions[left:right] = probabilities[i, :n]
    return predictions, len(dataset)


def temperature_fit(probabilities: np.ndarray, y: np.ndarray):
    p = np.clip(probabilities.astype(np.float64), 1e-6, 1 - 1e-6)
    z = logit(p)
    def objective(log_t):
        t = math.exp(float(log_t))
        scaled = z / t
        return float(np.mean(np.logaddexp(0, scaled) - y * scaled))
    result = minimize_scalar(objective, bounds=(math.log(0.05), math.log(20.0)),
                             method="bounded", options={"xatol": 1e-5})
    return math.exp(float(result.x)), float(result.fun)


def apply_temperature(probabilities: np.ndarray, temperature: float):
    p = np.clip(probabilities.astype(np.float64), 1e-6, 1 - 1e-6)
    return expit(logit(p) / temperature)


def learner_bootstrap(y: np.ndarray, probability: np.ndarray, groups: np.ndarray,
                      seed: int, draws: int = 1000):
    p = np.clip(probability.astype(np.float64), 1e-12, 1 - 1e-12)
    ll = -(y * np.log(p) + (1 - y) * np.log1p(-p))
    bs = np.square(p - y)
    acc = ((p >= 0.5) == y).astype(np.float64)
    n_groups = int(groups.max()) + 1
    counts = np.bincount(groups, minlength=n_groups).astype(np.float64)
    per = {}
    for name, values in (("log_loss", ll), ("brier", bs), ("accuracy", acc)):
        sums = np.bincount(groups, weights=values, minlength=n_groups)
        per[name] = sums / np.maximum(counts, 1)
    present = counts > 0
    rng = np.random.default_rng(seed)
    output = {}
    for name, values in per.items():
        values = values[present]
        sample_means = np.empty(draws, dtype=np.float64)
        for i in range(draws):
            sample_means[i] = rng.choice(values, size=len(values), replace=True).mean()
        output[name] = {"mean_per_learner": float(values.mean()),
                        "ci_95_percentile": [float(np.quantile(sample_means, .025)),
                                             float(np.quantile(sample_means, .975))],
                        "learners": int(len(values)), "bootstrap_draws": draws}
    return output


def build_reliability_svg(calibration_bins: dict[str, list[dict]], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 760, 560
    left, top, plot = 80, 40, 420
    colors = {"sgd_logistic": "#444444", "dkt": "#1f77b4", "sakt": "#d62728"}
    curves = []
    for name in ("sgd_logistic", "dkt", "sakt"):
        bins = calibration_bins.get(name, [])
        points = [(b["mean_probability"], b["observed_positive_rate"])
                  for b in bins if b["count"] > 0]
        if len(points) >= 2:
            coords = " ".join(f"{left+x*plot:.2f},{top+(1-y)*plot:.2f}" for x, y in points)
            curves.append(f'<polyline points="{coords}" fill="none" stroke="{colors[name]}" stroke-width="3"/>')
            for x, y in points:
                curves.append(f'<circle cx="{left+x*plot:.2f}" cy="{top+(1-y)*plot:.2f}" r="3.5" fill="{colors[name]}"/>')
    axes = [f'<line x1="{left}" y1="{top+plot}" x2="{left+plot}" y2="{top+plot}" stroke="#333"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot}" stroke="#333"/>',
            f'<line x1="{left}" y1="{top+plot}" x2="{left+plot}" y2="{top}" stroke="#888" stroke-dasharray="6,6"/>',
            f'<text x="{left+plot/2}" y="{height-28}" text-anchor="middle" font-size="14">Mean predicted probability</text>',
            f'<text x="20" y="{top+plot/2}" transform="rotate(-90 20 {top+plot/2})" text-anchor="middle" font-size="14">Observed correctness rate</text>']
    legend = []
    for i, name in enumerate(("sgd_logistic", "dkt", "sakt")):
        legend.append(f'<text x="{left+plot+24}" y="{top+32+i*26}" fill="{colors[name]}" font-size="13">{name}</text>')
    content = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
               '<rect width="100%" height="100%" fill="white"/>'
               '<text x="380" y="22" text-anchor="middle" font-size="17">Calibration on learner-held-out validation cohort</text>'
               + "".join(axes + curves + legend) + "</svg>\n")
    path.write_text(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path(os.environ.get("MCP_RI_DATA_DIR", ROOT / "data")))
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--seed", type=int, default=2025)
    parser.add_argument("--max-epochs", type=int, default=8)
    parser.add_argument("--patience", type=int, default=2)
    parser.add_argument("--batch-size-dkt", type=int, default=32)
    parser.add_argument("--batch-size-sakt", type=int, default=96)
    parser.add_argument("--max-sequence-length", type=int, default=200)
    parser.add_argument("--scan-batch-size", type=int, default=20000)
    parser.add_argument("--models", default="dkt,sakt", help="comma-separated: dkt,sakt")
    args = parser.parse_args(argv)
    if args.max_epochs < 1 or args.patience < 1 or args.max_sequence_length < 2:
        parser.error("epochs, patience, and sequence length must be positive")
    requested_models = [m.strip().lower() for m in args.models.split(",") if m.strip()]
    if not requested_models or set(requested_models) - {"dkt", "sakt"}:
        parser.error("--models accepts dkt and/or sakt")
    assert_training_feature_whitelist()
    data_root = args.data_root.expanduser()
    output_root = args.output_root.expanduser()
    processed = data_root / "processed/ednet/ednet_kt1_features.csv.gz"
    summary_path = data_root / "processed/ednet/ednet_preprocessing_summary.json"
    if not processed.is_file() or not summary_path.is_file():
        parser.error(f"processed EdNet data is missing under {data_root}")
    summary = json.loads(summary_path.read_text())
    split_summary = summary["split_protocols"]["unseen_learner"]
    train_prevalence = split_summary["train"]["correct_targets"] / split_summary["train"]["targets"]
    encoder = SparseFeatureEncoder.load(output_root / "models/preprocessing/ednet_sgd_preprocessor.json")
    rf_path = output_root / "models/trained/random_forest/phase7-20261104T121919Z-seed2025/model.joblib"
    xgb_path = output_root / "models/trained/xgboost/phase7-xgb-resume-20261105T040130Z-seed2025/model.json"
    required_artifacts = [rf_path, xgb_path, output_root / "models/trained/ednet_sgd_logistic.joblib"]
    missing = [str(p) for p in required_artifacts if not p.is_file()]
    if missing:
        parser.error(f"existing comparison artifacts are missing: {missing}")
    models = {
        "sgd_logistic": joblib.load(output_root / "models/trained/ednet_sgd_logistic.joblib"),
        "random_forest": joblib.load(rf_path),
        "xgboost_600": xgb.XGBClassifier(n_jobs=min(8, os.cpu_count() or 1)),
    }
    models["xgboost_600"].load_model(xgb_path)
    if hasattr(models["random_forest"], "n_jobs"):
        models["random_forest"].n_jobs = min(8, os.cpu_count() or 1)
        models["random_forest"].verbose = 0
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    exp_id = f"phase8-temporal-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-seed{args.seed}"
    report_dir = output_root / "results/reports" / exp_id
    model_root = output_root / "models/trained/sequence_models" / exp_id
    report_dir.mkdir(parents=True, exist_ok=False)
    model_root.mkdir(parents=True, exist_ok=False)
    run = {"id": exp_id, "status": "running",
           "target": "next submitted-answer correctness; behavioral response outcome only",
           "validation_protocol": "unseen learner; role groups are early-stop 10%, calibration 10%, report-only 80% by learner hash",
           "test_partition_used": False,
           "data": {"processed_file": str(processed), "bytes": processed.stat().st_size,
                    "raw_snapshot": summary.get("source_archives", {})},
           "training_sample": "same deterministic 5% unseen-learner training sample as Phase 6/7",
           "started_at_utc": datetime.now(timezone.utc).isoformat(),
           "configuration": {"seed": args.seed, "max_epochs": args.max_epochs,
                             "patience": args.patience, "max_sequence_length": args.max_sequence_length,
                             "batch_size_dkt": args.batch_size_dkt,
                             "batch_size_sakt": args.batch_size_sakt,
                             "optimizer": "AdamW(lr=1e-3, weight_decay=1e-5)",
                             "loss": "binary cross-entropy on each next response; padding masked",
                             "question_vocabulary": "train-only Phase 6 encoder vocabulary plus one unknown bucket",
                             "sequence_input": "question identity and recorded correctness of strictly prior submitted responses",
                             "current_target_answer_feature_used": False,
                             "current_elapsed_time_feature_used": False}}
    (report_dir / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    started = time.monotonic()
    try:
        print(f"Loading selected sequences and scoring existing models on validation; device={device}", flush=True)
        train_records, val_records, y_val, role, group, existing_probs, data_counts = load_sequences(
            processed, encoder, models, train_prevalence, args.seed, args.scan_batch_size)
        if len(y_val) != split_summary["validation"]["targets"]:
            raise ValueError(f"validation count mismatch: {len(y_val)} != {split_summary['validation']['targets']}")
        if not train_records or not val_records:
            raise ValueError("selected training or validation sequence set is empty")
        n_items = len(encoder.question_index) + 1
        role_counts = dict(zip(*np.unique(role, return_counts=True)))
        print(f"Train: {data_counts['train_target_interactions']:,} interactions, "
              f"{data_counts['train_learners']:,} learners; validation: {len(y_val):,} rows; "
              f"vocabulary={n_items:,}; role counts={role_counts}", flush=True)
        run["cohort"] = {**data_counts,
                         "train_learners_including_short_sequences": len(train_records),
                         "train_interactions": int(data_counts["train_target_interactions"]),
                         "validation_targets": len(y_val),
                         "validation_transitions_scored_by_sequence_models": int(sum(max(len(r.questions)-1, 0) for r in val_records)),
                         "validation_cold_start_rows_excluded_from_sequence_comparison": int(sum(len(r.questions) > 0 for r in val_records)),
                         "validation_role_examples": {"early_stop": int(np.sum(role == 0)),
                                                      "calibration": int(np.sum(role == 1)),
                                                      "report": int(np.sum(role == 2))},
                         "train_prevalence": train_prevalence,
                         "question_vocab_size_including_unknown": n_items,
                         "max_train_sequence_length": max(len(r.questions) for r in train_records),
                         "max_validation_sequence_length": max(len(r.questions) for r in val_records)}
        pred = {name: values.copy() for name, values in existing_probs.items()}
        training = {}
        sequence_windows = {}
        for name in requested_models:
            model_path = model_root / name / "model.pt"
            model_path.parent.mkdir(parents=True, exist_ok=False)
            model, train_result = train_one_model(
                name, train_records, val_records, n_items, device, model_path,
                args.seed, args.max_epochs, args.batch_size_dkt if name == "dkt" else args.batch_size_sakt,
                args.max_sequence_length, args.patience)
            training[name] = train_result
            model_prob, n_windows = predict_sequences(
                model, name, val_records, len(y_val),
                args.batch_size_dkt if name == "dkt" else args.batch_size_sakt,
                args.max_sequence_length, device)
            pred[name] = model_prob
            sequence_windows[name] = n_windows
            torch.save({"model": name, "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
                        "config": {"n_items": n_items, "max_length": args.max_sequence_length,
                                   "dim": 128, "seed": args.seed}}, model_path)
            del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        model_names = ["majority", "last_response", "historical_accuracy", "sgd_logistic",
                       "random_forest", "xgboost_600", *requested_models]
        valid_sequence_rows = np.isfinite(pred[requested_models[0]])
        for name in requested_models[1:]:
            valid_sequence_rows &= np.isfinite(pred[name])
        calibration_mask = (role == 1) & valid_sequence_rows
        report_mask = (role == 2) & valid_sequence_rows
        if not np.any(calibration_mask) or not np.any(report_mask):
            raise ValueError("calibration or report-only validation cohort is empty")
        calibrators = {}
        calibrated = {}
        for name in model_names:
            finite = np.isfinite(pred[name])
            cal_mask = calibration_mask & finite
            report_finite = report_mask & finite
            if not np.any(cal_mask) or not np.any(report_finite):
                continue
            temp, cal_nll = temperature_fit(pred[name][cal_mask], y_val[cal_mask])
            calibrators[name] = {"temperature": temp,
                                 "calibration_examples": int(np.sum(cal_mask)),
                                 "calibration_log_loss_after_scaling": cal_nll}
            calibrated[name] = apply_temperature(pred[name], temp).astype(np.float32)

        metrics = {}
        bins = {}
        bootstraps = {}
        for name in model_names:
            finite_report = report_mask & np.isfinite(pred[name])
            if not np.any(finite_report):
                continue
            y = y_val[finite_report]
            raw = pred[name][finite_report]
            raw_stats = classification_metrics(y, raw)
            metrics[name] = {"raw": raw_stats,
                             "report_examples": int(len(y)),
                             "report_learners": int(len(np.unique(group[finite_report])))}
            bins[name] = raw_stats["calibration_bins"]
            if name in calibrated:
                calibrated_p = calibrated[name][finite_report]
                calibrated_stats = classification_metrics(y, calibrated_p)
                metrics[name]["temperature_scaled"] = calibrated_stats
                bins[name + "_temperature_scaled"] = calibrated_stats["calibration_bins"]
            bootstraps[name] = learner_bootstrap(y, raw, group[finite_report], args.seed)
        logistic_name = "sgd_logistic"
        paired_differences = {}
        rng = np.random.default_rng(args.seed + 55)
        for name in requested_models:
            mask = report_mask & np.isfinite(pred[name]) & np.isfinite(pred[logistic_name])
            y = y_val[mask].astype(np.float64)
            p = np.clip(pred[name][mask].astype(np.float64), 1e-12, 1-1e-12)
            pl = np.clip(pred[logistic_name][mask].astype(np.float64), 1e-12, 1-1e-12)
            g = group[mask]
            present = np.unique(g)
            delta = {
                "log_loss": (-(y*np.log(p)+(1-y)*np.log1p(-p))) - (-(y*np.log(pl)+(1-y)*np.log1p(-pl))),
                "brier": np.square(p-y)-np.square(pl-y),
                "accuracy": ((p>=0.5)==y).astype(float)-((pl>=0.5)==y).astype(float),
            }
            ci = {}
            for metric_name, values in delta.items():
                counts = np.bincount(g, minlength=int(g.max())+1)
                sums = np.bincount(g, weights=values, minlength=len(counts))
                per_learner = sums[present]/np.maximum(counts[present],1)
                draws = np.empty(1000, dtype=np.float64)
                for j in range(len(draws)):
                    draws[j] = rng.choice(per_learner, size=len(per_learner), replace=True).mean()
                ci[metric_name] = {"mean_per_learner_difference_vs_logistic": float(per_learner.mean()),
                                   "ci_95_percentile": [float(np.quantile(draws,.025)),float(np.quantile(draws,.975))],
                                   "direction": "negative favors sequence model; positive favors logistic"}
            paired_differences[name] = ci

        report = {**run, "status": "complete",
                  "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                  "runtime_seconds": time.monotonic()-started,
                  "software": {"python": sys.version.split()[0], "torch": torch.__version__,
                              "cuda_runtime": torch.version.cuda,
                              "scikit_learn": __import__("sklearn").__version__,
                              "xgboost": xgb.__version__, "numpy": np.__version__},
                  "hardware": {"device": str(device),
                               "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                               "gpu_memory_bytes": torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else None,
                               "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
                  "models": training, "validation_sequence_windows": sequence_windows,
                  "temperature_scaling": calibrators,
                  "metrics": metrics, "learner_cluster_bootstrap": bootstraps,
                  "paired_learner_bootstrap_vs_logistic": paired_differences,
                  "test_partition_used": False,
                  "claims_boundary": "EdNet supplies interaction history and derived correctness only; results do not validate cognitive-state or representation-selection claims.",
                  "artifacts": {"models": str(model_root), "report": str(report_dir / "experiment.json")}}
        (report_dir / "experiment.json").write_text(json.dumps(report, indent=2) + "\n")
        columns = ["model", "calibration", "n_examples", "n_learners", "accuracy", "precision", "recall", "f1",
                   "roc_auc", "pr_auc_average_precision", "log_loss", "brier_score", "ece_equal_width"]
        with (report_dir / "validation_metrics.csv").open("w", newline="") as f:
            w = csv.writer(f); w.writerow(columns)
            for name, entry in metrics.items():
                for calibration in ("raw", "temperature_scaled"):
                    if calibration not in entry: continue
                    m = entry[calibration]
                    w.writerow([name, calibration, entry["report_examples"], entry["report_learners"],
                                m["accuracy"], m["precision_positive_correct"], m["recall_positive_correct"],
                                m["f1_positive_correct"], m["roc_auc"], m["pr_auc_average_precision"],
                                m["log_loss"], m["brier_score"], m["ece_equal_width"]])
        with (report_dir / "validation_calibration_bins.csv").open("w", newline="") as f:
            w = csv.writer(f); w.writerow(["model", "calibration", "lower", "upper", "count", "mean_probability", "observed_positive_rate"])
            for name, values in bins.items():
                label = "temperature_scaled" if name.endswith("_temperature_scaled") else "raw"
                clean_name = name.removesuffix("_temperature_scaled")
                for b in values:
                    w.writerow([clean_name, label, b["lower"], b["upper"], b["count"],
                                b["mean_probability"], b["observed_positive_rate"]])
        with (report_dir / "learner_bootstrap.csv").open("w", newline="") as f:
            w = csv.writer(f); w.writerow(["model", "metric", "mean_per_learner", "ci_lower", "ci_upper", "learners", "draws"])
            for name, values in bootstraps.items():
                for metric_name, interval in values.items():
                    w.writerow([name, metric_name, interval["mean_per_learner"], *interval["ci_95_percentile"],
                                interval["learners"], interval["bootstrap_draws"]])
        with (report_dir / "paired_learner_bootstrap_vs_logistic.csv").open("w", newline="") as f:
            w = csv.writer(f); w.writerow(["model", "metric", "mean_per_learner_difference", "ci_lower", "ci_upper", "interpretation"])
            for name, values in paired_differences.items():
                for metric_name, interval in values.items():
                    w.writerow([name, metric_name, interval["mean_per_learner_difference_vs_logistic"],
                                *interval["ci_95_percentile"], interval["direction"]])
        build_reliability_svg(bins, output_root / "results/figures" / f"{exp_id}_reliability.svg")
        (report_dir / "run.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"Sequence training complete: {exp_id}", flush=True)
        for name, entry in metrics.items():
            m = entry["raw"]
            print(name, " ".join(f"{k}={m[k]:.6f}" for k in
                  ("accuracy", "f1_positive_correct", "roc_auc", "pr_auc_average_precision",
                   "log_loss", "brier_score", "ece_equal_width")), flush=True)
        print(f"Report: {report_dir / 'experiment.json'}", flush=True)
    except Exception as error:
        run.update(status="failed", failure=f"{type(error).__name__}: {error}",
                   elapsed_seconds=time.monotonic()-started)
        (report_dir / "run.json").write_text(json.dumps(run, indent=2) + "\n")
        raise


if __name__ == "__main__":
    main()
