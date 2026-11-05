#!/usr/bin/env python3
"""Continue the saved Phase 7 XGBoost booster using the identical EdNet learner sample."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import resource
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import xgboost as xgb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "training"))
from mcp_ri.models.ednet_logistic import (  # noqa: E402
    SparseFeatureEncoder,
    assert_training_feature_whitelist,
    classification_metrics,
    row_is_training_sample,
)
from train_ednet_advanced import feature_groups, learner_bucket  # noqa: E402


def collect_training_and_early_stop(dataset: Path, encoder: SparseFeatureEncoder, *, seed: int, batch_size: int):
    """Single sequential read, preserving Phase 6 learner sample and validation learner subset."""
    train_chunks=[]; train_labels=[]; stop_chunks=[]; stop_labels=[]
    train_batch=[]; stop_batch=[]; learners=set(); stop_learners=set()
    counts=Counter()

    def flush(rows, xs, ys, kind):
        if not rows:
            return
        matrix,_=encoder.transform(rows)
        xs.append(matrix.astype(np.float32, copy=False))
        labels=np.fromiter((int(r["correctness"]) for r in rows),dtype=np.int8,count=len(rows))
        ys.append(labels)
        counts[kind]+=len(rows)
        rows.clear()

    with gzip.open(dataset,"rt",encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        required={"correctness","split_unseen_learner","learner_id"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"processed data missing required columns: {sorted(required-set(reader.fieldnames or []))}")
        for row in reader:
            if row_is_training_sample(row,seed=seed,sample_percent=5):
                train_batch.append(row);learners.add(row["learner_id"])
                if len(train_batch)>=batch_size:flush(train_batch,train_chunks,train_labels,"train_examples")
            elif row.get("split_unseen_learner")=="validation" and row.get("correctness") in {"0","1"} and learner_bucket(row.get("learner_id",""),seed,"phase7-es")<200:
                stop_batch.append(row);stop_learners.add(row["learner_id"])
                if len(stop_batch)>=batch_size:flush(stop_batch,stop_chunks,stop_labels,"early_stop_examples")
        flush(train_batch,train_chunks,train_labels,"train_examples")
        flush(stop_batch,stop_chunks,stop_labels,"early_stop_examples")
    if not train_chunks or not stop_chunks:
        raise ValueError("training or early-stopping partition is empty")
    x_train=sp.vstack(train_chunks,format="csr",dtype=np.float32)
    y_train=np.concatenate(train_labels)
    x_stop=sp.vstack(stop_chunks,format="csr",dtype=np.float32)
    y_stop=np.concatenate(stop_labels)
    if set(np.unique(y_train))!={0,1} or set(np.unique(y_stop))!={0,1}:
        raise ValueError("both classes are required in train and early-stop data")
    return x_train,y_train,x_stop,y_stop,{"training_examples":len(y_train),"training_learners":len(learners),"early_stopping_examples":len(y_stop),"early_stopping_learners":len(stop_learners),"training_matrix_nnz":int(x_train.nnz),"training_matrix_shape":list(x_train.shape),"early_stopping_matrix_nnz":int(x_stop.nnz),"early_stopping_matrix_shape":list(x_stop.shape)}


def validation_batches(dataset: Path, encoder: SparseFeatureEncoder, batch_size: int):
    with gzip.open(dataset,"rt",encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream);batch=[]
        for row in reader:
            if row.get("split_unseen_learner")=="validation" and row.get("correctness") in {"0","1"}:
                batch.append(row)
                if len(batch)>=batch_size:
                    yield batch;batch=[]
        if batch:yield batch


def probabilities(row, prevalence):
    last=row.get("previous_response_correctness","")
    hist=row.get("prior_accuracy","")
    return (float(last) if last else prevalence,float(hist) if hist else prevalence)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root",type=Path,default=Path(os.environ.get("MCP_RI_DATA_DIR",ROOT/"data")))
    parser.add_argument("--output-root",type=Path,default=ROOT)
    parser.add_argument("--seed",type=int,default=2025)
    parser.add_argument("--batch-size",type=int,default=20000)
    parser.add_argument("--additional-rounds",type=int,default=300)
    parser.add_argument("--early-stopping-rounds",type=int,default=30)
    parser.add_argument("--workers",type=int,default=min(8,os.cpu_count() or 1))
    args=parser.parse_args(argv)
    if args.additional_rounds<1 or args.early_stopping_rounds<1 or args.batch_size<1:
        parser.error("round counts and batch size must be positive")
    assert_training_feature_whitelist()
    data_root=args.data_root.expanduser();output=args.output_root.expanduser()
    dataset=data_root/"processed/ednet/ednet_kt1_features.csv.gz"
    summary=json.loads((data_root/"processed/ednet/ednet_preprocessing_summary.json").read_text())
    prevalence=summary["split_protocols"]["unseen_learner"]["train"]["correct_targets"]/summary["split_protocols"]["unseen_learner"]["train"]["targets"]
    encoder=SparseFeatureEncoder.load(output/"models/preprocessing/ednet_sgd_preprocessor.json")
    original_model_path=output/"models/trained/xgboost/phase7-20261104T100506Z-seed2025/model.json"
    if not dataset.is_file() or not original_model_path.is_file():
        parser.error("processed EdNet file or Phase 7 XGBoost checkpoint is missing")

    experiment_id=f"phase7-xgb-resume-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-seed{args.seed}"
    report_dir=output/"results/reports"/experiment_id
    model_dir=output/"models/trained/xgboost"/experiment_id
    report_dir.mkdir(parents=True,exist_ok=False);model_dir.mkdir(parents=True,exist_ok=False)
    run={"id":experiment_id,"status":"running","target":"next submitted-answer correctness; behavioral outcome only","resumed_from_model":str(original_model_path),"test_partition_used":False,"features":"identical Phase 6/7 feature whitelist and fitted encoder; no additional features","started_at_utc":datetime.now(timezone.utc).isoformat()}
    (report_dir/"run.json").write_text(json.dumps(run,indent=2)+"\n")
    wall_start=time.monotonic()
    try:
        fit_start=time.monotonic()
        x_train,y_train,x_stop,y_stop,sizes=collect_training_and_early_stop(dataset,encoder,seed=args.seed,batch_size=args.batch_size)
        matrix_seconds=time.monotonic()-fit_start
        print(f"Training examples {len(y_train):,}; early-stop examples {len(y_stop):,}; sparse shape {x_train.shape}, nnz {x_train.nnz:,}",flush=True)
        base=xgb.XGBClassifier();base.load_model(original_model_path)
        original_rounds=base.get_booster().num_boosted_rounds()
        if original_rounds!=300:
            raise ValueError(f"expected prior 300-round checkpoint, found {original_rounds} rounds")
        model=xgb.XGBClassifier(n_estimators=args.additional_rounds,learning_rate=0.05,max_depth=6,subsample=0.8,colsample_bytree=0.8,
            reg_lambda=5.0,reg_alpha=0.0,min_child_weight=10.0,scale_pos_weight=1.0,tree_method="hist",max_bin=128,
            objective="binary:logistic",eval_metric="logloss",early_stopping_rounds=args.early_stopping_rounds,
            n_jobs=args.workers,random_state=args.seed,verbosity=1)
        fit_start=time.monotonic()
        model.fit(x_train,y_train,eval_set=[(x_stop,y_stop)],xgb_model=base.get_booster(),verbose=False)
        continuation_seconds=time.monotonic()-fit_start
        model.save_model(model_dir/"model.json")
        total_rounds=model.get_booster().num_boosted_rounds()
        model_groups=feature_groups(encoder)
        raw_importance=model.get_booster().get_score(importance_type="gain")
        grouped=np.zeros(len(model_groups),dtype=np.float64)
        for col,value in raw_importance.items():
            try:grouped[int(col[1:])]=value
            except (ValueError,IndexError):pass
        totals=Counter()
        for name,value in zip(model_groups,grouped):totals[name]+=float(value)
        denom=sum(totals.values()) or 1
        importance=[{"feature_group":name,"importance":value,"normalized_importance":value/denom} for name,value in totals.most_common()]
        (model_dir/"grouped_gain_importance.json").write_text(json.dumps(importance,indent=2)+"\n")

        old=xgb.XGBClassifier();old.load_model(original_model_path)
        logit=__import__("joblib").load(output/"models/trained/ednet_sgd_logistic.joblib")
        names=["majority","last_response","historical_accuracy","sgd_logistic","xgboost_300_round","xgboost_resumed"]
        stored={name:[] for name in names};targets=[];validation_count=0;scoring_start=time.monotonic()
        for batch in validation_batches(dataset,encoder,args.batch_size):
            y=np.fromiter((int(row["correctness"]) for row in batch),dtype=np.int8,count=len(batch))
            matrix,_=encoder.transform(batch)
            prior=[];history=[]
            for row in batch:
                a,b=probabilities(row,prevalence);prior.append(a);history.append(b)
            stored["majority"].append(np.full(len(y),prevalence,dtype=np.float32))
            stored["last_response"].append(np.asarray(prior,dtype=np.float32))
            stored["historical_accuracy"].append(np.asarray(history,dtype=np.float32))
            stored["sgd_logistic"].append(logit.predict_proba(matrix)[:,1].astype(np.float32))
            stored["xgboost_300_round"].append(old.predict_proba(matrix)[:,1].astype(np.float32))
            stored["xgboost_resumed"].append(model.predict_proba(matrix)[:,1].astype(np.float32))
            targets.append(y);validation_count+=len(y)
            if validation_count and validation_count%1_000_000<len(y):print(f"Full validation scored: {validation_count:,}",flush=True)
        scoring_seconds=time.monotonic()-scoring_start
        y=np.concatenate(targets);metrics={}
        for name,chunks in stored.items():metrics[name]=classification_metrics(y,np.concatenate(chunks))
        columns=["accuracy","precision_positive_correct","recall_positive_correct","f1_positive_correct","roc_auc","pr_auc_average_precision","log_loss","brier_score","ece_equal_width"]
        with (report_dir/"validation_metrics.csv").open("w",newline="") as f:
            writer=csv.writer(f);writer.writerow(["model",*columns,"n_examples"])
            for name,values in metrics.items():writer.writerow([name,*[values[c] for c in columns],values["n_examples"]])
        with (report_dir/"calibration_bins.csv").open("w",newline="") as f:
            writer=csv.writer(f);writer.writerow(["model","lower","upper","count","mean_probability","observed_positive_rate"])
            for name,values in metrics.items():
                for b in values["calibration_bins"]:writer.writerow([name,b["lower"],b["upper"],b["count"],b["mean_probability"],b["observed_positive_rate"]])
        report={**run,"status":"complete","finished_at_utc":datetime.now(timezone.utc).isoformat(),"dataset":{"processed_path":str(dataset),**sizes,"validation_examples":validation_count,"validation_protocol":"unseen learner"},"configuration":{"xgboost_version":xgb.__version__,"prior_rounds":original_rounds,"additional_rounds_max":args.additional_rounds,"total_rounds":total_rounds,"best_iteration":int(model.best_iteration),"early_stopping_rounds":args.early_stopping_rounds,"early_stopping_metric":"validation logloss","learning_rate":0.05,"max_depth":6,"subsample":0.8,"colsample_bytree":0.8,"reg_lambda":5.0,"reg_alpha":0.0,"min_child_weight":10.0,"scale_pos_weight":1.0,"tree_method":"hist","max_bin":128,"seed":args.seed,"n_jobs":args.workers,"encoder_path":str(output/"models/preprocessing/ednet_sgd_preprocessor.json")},"timing_seconds":{"matrix_construction_single_pass":matrix_seconds,"continued_fit":continuation_seconds,"full_validation_scoring":scoring_seconds,"total_wall":time.monotonic()-wall_start},"peak_process_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"metrics":metrics,"feature_importance":importance,"interpretation":"Gain importance reports model split usage, not causal contribution; cardinality and correlated features affect rankings.","test_partition_used":False,"artifacts":{"model":str(model_dir/"model.json"),"importance":str(model_dir/"grouped_gain_importance.json"),"report":str(report_dir/"experiment.json"),"metrics_csv":str(report_dir/"validation_metrics.csv"),"calibration_csv":str(report_dir/"calibration_bins.csv")}}
        (report_dir/"experiment.json").write_text(json.dumps(report,indent=2)+"\n")
        (report_dir/"run.json").write_text(json.dumps(report,indent=2)+"\n")
        print(f"Resume complete: {original_rounds} -> {total_rounds} rounds; best_iteration={model.best_iteration}; report={report_dir/'experiment.json'}",flush=True)
        for name,value in metrics.items():print(name,*(f"{key}={value[key]:.6f}" for key in ("accuracy","f1_positive_correct","roc_auc","pr_auc_average_precision","log_loss","brier_score","ece_equal_width")))
    except Exception as error:
        run.update(status="failed",failure=f"{type(error).__name__}: {error}",elapsed_seconds=time.monotonic()-wall_start)
        (report_dir/"run.json").write_text(json.dumps(run,indent=2)+"\n")
        raise


if __name__=="__main__":main()
