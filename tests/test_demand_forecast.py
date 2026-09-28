"""Forecasting checks run on published, aggregated results, no private raw CSV needed."""
import sys, unittest, json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from demand_forecast import forecast, wape, METHODS, VALIDATION_ORIGINS, TEST_ORIGIN

class DemandForecastTests(unittest.TestCase):
    def test_forecast_only_uses_training_history(self):
        # Changing values beyond a historical cutoff cannot change an earlier forecast.
        pre=np.arange(1,27,dtype=float)*2
        first=np.r_[pre,[100,200,400,900]]
        second=np.r_[pre,[9000,8000,7000,6000]]
        for m in METHODS:
            np.testing.assert_array_equal(forecast(first[:26],m),forecast(second[:26],m))

    def test_nonnegative_four_week_forecasts(self):
        trailing=np.array([200,200,150,150,75,50,5,0],float)
        for method in METHODS:
            out=forecast(trailing,method)
            self.assertEqual(len(out),4)
            self.assertTrue(np.isfinite(out).all())
            self.assertTrue((out>=0).all())

    def test_baseline_and_wape_definition(self):
        np.testing.assert_allclose(forecast(np.arange(1,9),'four_week_mean'),[6.5]*4)
        np.testing.assert_allclose(forecast(np.arange(1,9),'four_week_repeat'),[5,6,7,8])
        self.assertAlmostEqual(wape(np.array([5,10]),np.array([7,8])),100*4/15)
        self.assertTrue(np.isnan(wape(np.array([0,0]),np.array([0,0]))))

    def test_expanding_folds_end_before_test(self):
        self.assertLess(max(VALIDATION_ORIGINS)+pd.Timedelta(weeks=4),TEST_ORIGIN)
        self.assertEqual([v.strftime('%Y-%m-%d') for v in VALIDATION_ORIGINS],
            ['2011-05-30','2011-06-27','2011-07-25','2011-08-22','2011-09-19'])

    def test_published_aggregates_reconcile(self):
        test=pd.read_csv(ROOT/'results/forecast_holdout_weeks.csv')
        summary=json.loads((ROOT/'results/forecast_summary.json').read_text())
        aggregate=next(x for x in summary['results'] if x['Series']=='All products')
        series=test.loc[test.Series=='All products']
        self.assertEqual(len(series),4)
        self.assertEqual(series.ActualUnits.sum(),aggregate['ActualTotal'])
        self.assertAlmostEqual(wape(series.ActualUnits.to_numpy(),series.ForecastUnits.to_numpy()),aggregate['HoldoutWAPE'],places=1)
        self.assertAlmostEqual(wape(series.ActualUnits.to_numpy(),series.BaselineUnits.to_numpy()),aggregate['BaselineHoldoutWAPE'],places=1)
        self.assertEqual(len(summary['sku_list']),5)

    def test_no_partial_weeks_and_zero_observed_holiday(self):
        h=pd.read_csv(ROOT/'results/forecast_weekly_history.csv')
        self.assertEqual(h.WeekStart.iloc[0],'2010-12-06')
        self.assertEqual(h.WeekStart.iloc[-1],'2011-11-28')
        self.assertEqual(len(h),52)
        self.assertEqual(int(h.set_index('WeekStart').loc['2010-12-27','All products']),0)

if __name__=='__main__':unittest.main()
