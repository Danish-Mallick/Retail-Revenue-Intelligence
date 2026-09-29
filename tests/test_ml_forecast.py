"""ML forecasting regression / leakage tests against published evidence."""
import json,sys,unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from ml_forecast_comparison import (FEATURE_NAMES,ML_METHODS,ALL_METHODS,
                                     features,panel_training,FORECAST_WEEKS)
from demand_forecast import VALIDATION_ORIGINS,TEST_ORIGIN

class TestMLForecast(unittest.TestCase):
 def test_features_only_depend_on_supplied_past(self):
  hist=np.array([40,50,60,80,100,110,105,99.],dtype=float)
  f1=features(hist,pd.Timestamp('2011-09-19'),3,False)
  f2=features(np.r_[hist,[9999.,.3]][:8],pd.Timestamp('2011-09-19'),3,False)
  np.testing.assert_array_equal(f1,f2)
  self.assertEqual(len(f1),len(FEATURE_NAMES))
  self.assertTrue(np.isfinite(f1).all())

 def test_panel_training_never_uses_targets_after_origin(self):
  weeks=pd.date_range('2011-01-03',periods=22,freq='W-MON')
  t=weeks[17]
  before=np.vstack([np.arange(22,dtype=float)+100,np.arange(22,dtype=float)*2+9])
  changed=before.copy();changed[:,17:]=1e8
  a=panel_training(weeks,before,t)
  b=panel_training(weeks,changed,t)
  for x,y in zip(a,b):np.testing.assert_array_equal(x,y)
  self.assertEqual(a[0].shape[1],len(FEATURE_NAMES))

 def test_time_windows_and_candidate_pool(self):
  self.assertEqual(len(VALIDATION_ORIGINS),5)
  self.assertLess(VALIDATION_ORIGINS[-1]+pd.Timedelta(weeks=4),TEST_ORIGIN)
  self.assertEqual(set(ML_METHODS),{'random_forest','xgboost'})
  self.assertEqual(FORECAST_WEEKS,4)

 def test_saved_validation_selection_not_test_selection(self):
  r=pd.read_csv(ROOT/'results/ml_holdout_comparison.csv')
  vals=pd.read_csv(ROOT/'results/ml_validation_folds.csv')
  self.assertEqual(len(vals),6*5*5)
  self.assertEqual(len(r),6*5)
  self.assertEqual(set(r.Method),set(ALL_METHODS))
  self.assertEqual(set(vals.Origin),{d.date().isoformat() for d in VALIDATION_ORIGINS})
  for label,g in r.groupby('Series'):
   selected=g.loc[g.SelectedByValidation]
   self.assertEqual(len(selected),1)
   self.assertAlmostEqual(selected.ValidationWAPE.iloc[0],g.ValidationWAPE.min(),places=4)
  # Core finding: validation preference did not match the best test score.
  s=r.query('Series == "All products"').set_index('Method')
  self.assertTrue(bool(s.loc['random_forest','SelectedByValidation']))
  self.assertLess(s.loc['eight_week_damped_trend','HoldoutWAPE'],s.loc['random_forest','HoldoutWAPE'])

 def test_powerbi_fourth_comparison_page_and_embedded_tables(self):
  root=ROOT/'powerbi'
  pages=json.loads((root/'Retail_Revenue_Intelligence.Report/definition/pages/pages.json').read_text())
  self.assertEqual(len(pages['pageOrder']),4)
  self.assertTrue((root/'Retail_Revenue_Intelligence.Report/definition/pages/fbd63632ebd44af2924e/page.json').exists())
  self.assertTrue((root/'Retail_Revenue_Intelligence.SemanticModel/definition/tables/MLModelScores.tmdl').exists())
  self.assertTrue((root/'Retail_Revenue_Intelligence.SemanticModel/definition/tables/MLHoldout.tmdl').exists())

 def test_published_holdout_aggregate_matches_original_experiment(self):
  old=json.loads((ROOT/'results/forecast_summary.json').read_text())
  df=pd.read_csv(ROOT/'results/ml_holdout_comparison.csv').query('Series == "All products"').set_index('Method')
  original=next(v for v in old['results'] if v['Series']=='All products')
  self.assertEqual(int(df.loc['four_week_mean','ActualTotal']),429081)
  self.assertAlmostEqual(df.loc['four_week_mean','HoldoutWAPE'],original['BaselineHoldoutWAPE'],places=1)
  self.assertAlmostEqual(df.loc['eight_week_damped_trend','HoldoutWAPE'],original['HoldoutWAPE'],places=1)
  h=pd.read_csv(ROOT/'results/ml_holdout_weeks.csv')
  self.assertEqual(len(h),6*5*4)
  self.assertEqual(len(h.query('Series == "All products"').WeekStart.unique()),4)

if __name__=='__main__':unittest.main()
