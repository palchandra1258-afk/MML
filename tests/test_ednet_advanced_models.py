import sys
import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np
import scipy.sparse as sp
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "training"))
from mcp_ri.models.ednet_logistic import SparseFeatureEncoder, classification_metrics, row_is_training_sample
from train_ednet_advanced import feature_groups, learner_bucket


class AdvancedModelsTests(unittest.TestCase):
    def test_shared_feature_encoder_is_sparse_and_stable(self):
        encoder = SparseFeatureEncoder()
        rows = [
            {"current_question_id":"q1", "current_part":"1", "current_skill_tags":"a;b", "n_prior_logged_events":"2", "prior_accuracy":"0.5"},
            {"current_question_id":"q2", "current_part":"2", "current_skill_tags":"b", "n_prior_logged_events":"3", "prior_accuracy":""},
        ]
        encoder.fit_batch(rows); encoder.finalize()
        x1,_=encoder.transform(rows); x2,_=SparseFeatureEncoder.from_dict(encoder.to_dict()).transform(rows)
        self.assertTrue(sp.isspmatrix_csr(x1)); self.assertEqual(x1.shape,x2.shape)
        self.assertTrue(np.array_equal(x1.toarray(),x2.toarray()))
        self.assertEqual(len(feature_groups(encoder)),encoder.n_features)

    def test_learner_sample_and_early_stop_selection_are_deterministic(self):
        row={"split_unseen_learner":"train","correctness":"1","learner_id":"user-42"}
        self.assertEqual(row_is_training_sample(row,seed=2025,sample_percent=5),row_is_training_sample(row,seed=2025,sample_percent=5))
        self.assertEqual(learner_bucket("user-42",2025,"phase7-es"),learner_bucket("user-42",2025,"phase7-es"))
        self.assertNotEqual(learner_bucket("user-42",2025,"phase7-es"),learner_bucket("user-42",2025,"other"))
        row["split_unseen_learner"]="test"
        self.assertFalse(row_is_training_sample(row,seed=2025,sample_percent=5))

    def test_random_forest_save_load_prediction_reproducible(self):
        rng=np.random.default_rng(17); x=sp.csr_matrix(rng.normal(size=(120,12)).astype(np.float32)); y=(x[:,0].toarray().ravel()+x[:,1].toarray().ravel()>0).astype(np.int8)
        a=RandomForestClassifier(n_estimators=8,max_depth=4,min_samples_leaf=2,n_jobs=1,random_state=9).fit(x,y)
        b=RandomForestClassifier(n_estimators=8,max_depth=4,min_samples_leaf=2,n_jobs=1,random_state=9).fit(x,y)
        self.assertTrue(np.array_equal(a.predict_proba(x),b.predict_proba(x)))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"rf.joblib";joblib.dump(a,p);loaded=joblib.load(p)
            pred=loaded.predict_proba(x)
        self.assertEqual(pred.shape,(120,2));self.assertTrue(np.all(np.isfinite(pred)))

    def test_xgboost_sparse_fit_save_load_and_metric(self):
        import xgboost as xgb
        rng=np.random.default_rng(21); x=sp.csr_matrix(rng.normal(size=(160,10)).astype(np.float32)); y=(x[:,0].toarray().ravel()>0).astype(np.int8)
        model=xgb.XGBClassifier(n_estimators=12,max_depth=2,learning_rate=.2,tree_method="hist",n_jobs=1,random_state=4,eval_metric="logloss")
        model.fit(x[:120],y[:120],eval_set=[(x[120:],y[120:])],verbose=False)
        pred=model.predict_proba(x[120:])[:,1]
        self.assertEqual(pred.shape,(40,));self.assertTrue(np.all((pred>=0)&(pred<=1)))
        values=classification_metrics(y[120:],pred)
        self.assertEqual(values["n_examples"],40);self.assertIn("ece_equal_width",values)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"xgb.json";model.save_model(p)
            loaded=xgb.XGBClassifier();loaded.load_model(p)
            self.assertTrue(np.allclose(pred,loaded.predict_proba(x[120:])[:,1]))

    def test_xgboost_continuation_appends_rounds_from_checkpoint(self):
        import xgboost as xgb
        rng=np.random.default_rng(31);x=sp.csr_matrix(rng.normal(size=(240,8)).astype(np.float32));y=(x[:,0].toarray().ravel()>0).astype(np.int8)
        first=xgb.XGBClassifier(n_estimators=6,max_depth=2,learning_rate=.1,tree_method="hist",n_jobs=1,random_state=4,eval_metric="logloss")
        first.fit(x[:180],y[:180])
        resumed=xgb.XGBClassifier(n_estimators=5,max_depth=2,learning_rate=.1,tree_method="hist",n_jobs=1,random_state=4,eval_metric="logloss",early_stopping_rounds=2)
        resumed.fit(x[:180],y[:180],eval_set=[(x[180:],y[180:])],xgb_model=first.get_booster(),verbose=False)
        self.assertEqual(first.get_booster().num_boosted_rounds(),6)
        self.assertEqual(resumed.get_booster().num_boosted_rounds(),11)
        self.assertGreaterEqual(resumed.best_iteration,6)


if __name__ == "__main__": unittest.main()
