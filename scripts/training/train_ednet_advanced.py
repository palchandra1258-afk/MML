#!/usr/bin/env python3
"""Train sparse Random Forest and XGBoost comparisons on the fixed EdNet sample."""
from __future__ import annotations

import argparse, csv, gzip, hashlib, json, os, resource, sys, time
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

import joblib
import numpy as np
import scipy.sparse as sp
import sklearn
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from mcp_ri.models.ednet_logistic import SparseFeatureEncoder, classification_metrics, row_is_training_sample, assert_training_feature_whitelist

def learner_bucket(learner_id: str, seed: int, namespace: str) -> int:
    digest = hashlib.blake2b(f"{namespace}:{seed}:{learner_id}".encode(), digest_size=8, person=b"mcp-ri-samp").digest()
    return int.from_bytes(digest, "big") % 10_000

def chunks(path: Path, predicate, size: int):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "correctness" not in reader.fieldnames:
            raise ValueError("missing correctness field in processed data")
        batch=[]
        for row in reader:
            if predicate(row):
                batch.append(row)
                if len(batch) >= size:
                    yield batch; batch=[]
        if batch: yield batch

def matrix_for(path, encoder, predicate, size, collect_y=True, limit=None):
    xs=[]; ys=[]; n=0
    for batch in chunks(path, predicate, size):
        x,_=encoder.transform(batch); xs.append(x)
        ys.append(np.fromiter((int(r["correctness"]) for r in batch),dtype=np.int8,count=len(batch)))
        n += len(batch)
        if limit and n >= limit: break
        if n and n % 500_000 < len(batch): print(f"Prepared {n:,} rows",flush=True)
    if not xs: raise ValueError("selected partition is empty")
    x=sp.vstack(xs,format="csr",dtype=np.float32)
    y=np.concatenate(ys) if collect_y else None
    return x,y,n

def feature_groups(encoder):
    d=encoder.to_dict(); q=len(d["question_ids"])+1; p=len(d["parts"])+1; t=len(d["skill_tags"])+2
    fields=d["numeric_fields"]
    groups=[]; names=[]
    for name,count in (("current_question_id",q),("current_part",p),("current_skill_tags",t)):
        groups.extend([name]*count)
    groups.extend(fields); groups.extend([f"{n}__missing" for n in fields])
    names.extend(groups)
    return names

def grouped_importance(model, names, importance):
    totals=Counter()
    for name,value in zip(names,importance): totals[name]+=float(value)
    denom=sum(totals.values()) or 1
    return [{"feature_group":k,"importance":v,"normalized_importance":v/denom} for k,v in totals.most_common()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-root",type=Path,default=Path(os.environ.get("MCP_RI_DATA_DIR",ROOT/"data")))
    ap.add_argument("--output-root",type=Path,default=ROOT)
    ap.add_argument("--seed",type=int,default=2025); ap.add_argument("--batch-size",type=int,default=20000)
    ap.add_argument("--workers",type=int,default=min(8,os.cpu_count() or 1))
    ap.add_argument("--models",choices=["all","random_forest","xgboost"],default="all")
    args=ap.parse_args(); assert_training_feature_whitelist()
    try:
        import xgboost as xgb
    except ImportError:
        xgb=None
    if args.models in ("all","xgboost") and xgb is None:
        ap.error("XGBoost unavailable in this interpreter; install requirements-training.txt")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    exp_id=f"phase7-{stamp}-seed{args.seed}"
    out=args.output_root.expanduser(); data=args.data_root.expanduser()/"processed/ednet/ednet_kt1_features.csv.gz"
    enc_path=out/"models/preprocessing/ednet_sgd_preprocessor.json"
    summary=json.loads((args.data_root.expanduser()/"processed/ednet/ednet_preprocessing_summary.json").read_text())
    encoder=SparseFeatureEncoder.load(enc_path)
    prevalence=summary["split_protocols"]["unseen_learner"]["train"]["correct_targets"]/summary["split_protocols"]["unseen_learner"]["train"]["targets"]
    run_dir=out/"results/reports"/exp_id; run_dir.mkdir(parents=True,exist_ok=False)
    model_dirs={"random_forest":out/"models/trained/random_forest"/exp_id,"xgboost":out/"models/trained/xgboost"/exp_id}
    for p in model_dirs.values(): p.mkdir(parents=True,exist_ok=False)
    test_config={"id":exp_id,"status":"running","target":"correctness of submitted answer, behavioral outcome","test_partition_used":False,"features":"same serialized logistic encoder and whitelist; no added features","sample":"same 5% learner hash subset as Phase 6; training learners only","started_at_utc":datetime.now(timezone.utc).isoformat()}
    (run_dir/"run.json").write_text(json.dumps(test_config,indent=2)+"\n")
    t0=time.monotonic()
    try:
        train_pred=lambda r: row_is_training_sample(r,seed=args.seed,sample_percent=5)
        xtr,ytr,ntr=matrix_for(data,encoder,train_pred,args.batch_size)
        print(f"Training matrix: {xtr.shape}, nnz={xtr.nnz:,}, {xtr.data.nbytes/1e9:.2f} GB values",flush=True)
        val_pred=lambda r:r.get("split_unseen_learner")=="validation" and r.get("correctness") in {"0","1"}
        # Early stopping uses a deterministic 2% of validation learners; final metrics below use every validation example.
        if args.models in ("all","xgboost"):
            es_pred=lambda r:val_pred(r) and learner_bucket(r.get("learner_id",""),args.seed,"phase7-es")<200
            xes,yes,nes=matrix_for(data,encoder,es_pred,args.batch_size)
            print(f"Early-stop subset: {len(yes):,} examples",flush=True)
        results={}; configs={}; importances={}; times={}
        if args.models in ("all","random_forest"):
            model=RandomForestClassifier(n_estimators=24,max_depth=12,min_samples_leaf=500,max_features="sqrt",
                class_weight=None,bootstrap=True,max_samples=0.5,n_jobs=args.workers,random_state=args.seed,
                verbose=1)
            t=time.monotonic(); model.fit(xtr,ytr); times["random_forest"]=time.monotonic()-t
            results["random_forest"]=model
            joblib.dump(model,model_dirs["random_forest"]/"model.joblib",compress=2)
            names=feature_groups(encoder); importances["random_forest"]=grouped_importance(model,names,model.feature_importances_)
            (model_dirs["random_forest"]/"grouped_importance.json").write_text(json.dumps(importances["random_forest"],indent=2)+"\n")
            configs["random_forest"]={"n_estimators":24,"max_depth":12,"min_samples_leaf":500,"max_features":"sqrt","class_weight":None,"bootstrap":True,"max_samples":0.5,"n_jobs":args.workers,"input":"CSR sparse; sklearn internal sparse handling"}
        if args.models in ("all","xgboost"):
            model=xgb.XGBClassifier(n_estimators=300,learning_rate=0.05,max_depth=6,subsample=0.8,colsample_bytree=0.8,
                reg_lambda=5.0,reg_alpha=0.0,min_child_weight=10.0,scale_pos_weight=1.0,tree_method="hist",
                max_bin=128,objective="binary:logistic",eval_metric="logloss",early_stopping_rounds=20,
                n_jobs=args.workers,random_state=args.seed,verbosity=1)
            t=time.monotonic(); model.fit(xtr,ytr,eval_set=[(xes,yes)],verbose=False); times["xgboost"]=time.monotonic()-t
            results["xgboost"]=model
            model.save_model(str(model_dirs["xgboost"]/"model.json"))
            names=feature_groups(encoder); scores=model.get_booster().get_score(importance_type="gain")
            vals=np.zeros(len(names),dtype=np.float64)
            for key,val in scores.items():
                try: vals[int(key[1:])]=val
                except (ValueError,IndexError): pass
            importances["xgboost"]=grouped_importance(model,names,vals)
            (model_dirs["xgboost"]/"grouped_gain_importance.json").write_text(json.dumps(importances["xgboost"],indent=2)+"\n")
            configs["xgboost"]={"n_estimators_max":300,"best_iteration":int(model.best_iteration),"early_stopping_rounds":20,"learning_rate":0.05,"max_depth":6,"subsample":0.8,"colsample_bytree":0.8,"reg_lambda":5.0,"reg_alpha":0.0,"min_child_weight":10.0,"scale_pos_weight":1.0,"tree_method":"hist","max_bin":128,"n_jobs":args.workers,"early_stopping_subset_examples":nes,"input":"CSR sparse matrix"}
        # A complete, one-pass validation score, including the original frozen logistic model and reference baselines.
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, log_loss
        stored={k:[] for k in ["majority","last_response","historical_accuracy","sgd_logistic",*results.keys()]}
        ys=[]; val_n=0
        old_logit=joblib.load(out/"models/trained/ednet_sgd_logistic.joblib")
        for batch in chunks(data,val_pred,args.batch_size):
            y=np.fromiter((int(r["correctness"]) for r in batch),dtype=np.int8,count=len(batch)); x,_=encoder.transform(batch)
            ys.append(y); stored["majority"].append(np.full(len(y),prevalence,dtype=np.float32))
            stored["last_response"].append(np.fromiter((float(r["previous_response_correctness"]) if r.get("previous_response_correctness","") else prevalence for r in batch),dtype=np.float32,count=len(batch)))
            stored["historical_accuracy"].append(np.fromiter((float(r["prior_accuracy"]) if r.get("prior_accuracy","") else prevalence for r in batch),dtype=np.float32,count=len(batch)))
            stored["sgd_logistic"].append(old_logit.predict_proba(x)[:,1].astype(np.float32))
            if "random_forest" in results: stored["random_forest"].append(results["random_forest"].predict_proba(x)[:,1].astype(np.float32))
            if "xgboost" in results: stored["xgboost"].append(results["xgboost"].predict_proba(x)[:,1].astype(np.float32))
            val_n+=len(y)
            if val_n%1_000_000<len(y): print(f"Scored validation {val_n:,}",flush=True)
        y=np.concatenate(ys); metrics={}
        for key,pieces in stored.items():
            p=np.clip(np.concatenate(pieces).astype(np.float64),1e-15,1-1e-15); pred=(p>=0.5).astype(np.int8)
            base=classification_metrics(y,p)
            metrics[key]=base
        with (run_dir/"validation_metrics.csv").open("w",newline="") as f:
            w=csv.writer(f); keys=["accuracy","precision_positive_correct","recall_positive_correct","f1_positive_correct","roc_auc","pr_auc_average_precision","log_loss","brier_score","ece_equal_width"]
            w.writerow(["model",*keys,"n_examples"])
            for key,v in metrics.items():w.writerow([key,*[v[k] for k in keys],v["n_examples"]])
        with (run_dir/"calibration_bins.csv").open("w",newline="") as f:
            w=csv.writer(f);w.writerow(["model","lower","upper","count","mean_probability","observed_positive_rate"])
            for key,v in metrics.items():
                for b in v["calibration_bins"]:w.writerow([key,b["lower"],b["upper"],b["count"],b["mean_probability"],b["observed_positive_rate"]])
        for model_name, vals in importances.items():
            with (run_dir/f"{model_name}_grouped_importance.csv").open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["feature_group","importance","normalized_importance"]);w.writeheader();w.writerows(vals)
        report={**test_config,"status":"complete","finished_at_utc":datetime.now(timezone.utc).isoformat(),"dataset":{"processed_path":str(data),"training_examples":ntr,"training_learners":27310,"training_matrix_shape":xtr.shape,"training_matrix_nnz":int(xtr.nnz),"validation_examples":val_n,"validation_early_stopping_examples":nes if args.models in ("all","xgboost") else None},"configuration":configs,"training_seconds":times,"wall_seconds":time.monotonic()-t0,"max_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"versions":{"scikit_learn":sklearn.__version__,"xgboost":getattr(xgb,"__version__",None)},"metrics":metrics,"feature_importance":importances,"interpretation":"Impurity/gain importance describes model split usage, not causal effects; high-cardinality categorical groups have more opportunities for splits.","test_partition_used":False,"artifacts":{"models":{k:str(v) for k,v in model_dirs.items()},"report":str(run_dir)}}
        (run_dir/"experiment.json").write_text(json.dumps(report,indent=2)+"\n")
        (run_dir/"run.json").write_text(json.dumps(report,indent=2)+"\n")
        print(f"Experiment {exp_id} complete; full validation n={val_n:,}; outputs {run_dir}")
        for name,v in metrics.items():print(name,*(f"{k}={v[k]:.5f}" for k in ("accuracy","f1_positive_correct","roc_auc","pr_auc_average_precision","log_loss","brier_score","ece_equal_width")))
    except Exception as e:
        test_config.update(status="failed",failure=f"{type(e).__name__}: {e}",elapsed_seconds=time.monotonic()-t0)
        (run_dir/"run.json").write_text(json.dumps(test_config,indent=2)+"\n"); raise

if __name__=="__main__": main()
