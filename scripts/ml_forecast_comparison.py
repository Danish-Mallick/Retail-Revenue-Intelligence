"""Compare Random Forest and XGBoost with statistical forecasts, using only past data.

Forecasts are four *direct* horizons (weeks 1..4), not a randomly shuffled
train/test split or a one-week model that reads true future lags. Fixed ML
hyperparameters are chosen in advance; five 4-week historical origins select
one method for each reported series. Nov 7–Dec 4 2011 is never used to select.

The data are a filtered transaction extract of *observed units sold*, not
unconstrained demand. Raw transactions are never exported to the repository.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from analyze import ROOT, fix_dates, load_extract
from demand_forecast import (FIRST_WEEK, LAST_WEEK, VALIDATION_ORIGINS,
                             TEST_ORIGIN, FORECAST_WEEKS, METHODS, forecast, wape)

ML_METHODS = ('random_forest', 'xgboost')
ALL_METHODS = METHODS + ML_METHODS
FEATURE_NAMES = (
    'horizon','lag_1_ratio','lag_2_ratio','lag_3_ratio','lag_4_ratio',
    'lag_5_ratio','lag_6_ratio','lag_7_ratio','lag_8_ratio',
    'mean_4_ratio','mean_8_ratio','std_4_ratio','std_8_ratio',
    'recent_vs_prior_4','positive_weeks_4','positive_weeks_8',
    'log_recent_scale','log_mean_8','target_week_of_year','target_month',
    'is_all_products',
)
SEED=42
POOL_SIZE=120 # fixed using ONLY the pre-validation cutoff
MIN_ACTIVE_WEEKS=12


def prepare_series(source:Path, pool_size:int=POOL_SIZE):
    raw=load_extract(source)
    _, corrected, _=fix_dates(raw)
    raw['WeekStart']=corrected.dt.to_period('W-SUN').dt.start_time
    weeks=pd.date_range(FIRST_WEEK,LAST_WEEK,freq='W-MON')
    initial=raw.loc[(raw.WeekStart>=FIRST_WEEK)&(raw.WeekStart<VALIDATION_ORIGINS[0])]
    popularity=initial.groupby('StockCode').agg(
        Orders=('InvoiceNo','nunique'),ActiveWeeks=('WeekStart','nunique'))
    eligible=popularity.loc[popularity.ActiveWeeks>=MIN_ACTIVE_WEEKS]
    pool=eligible.sort_values(['Orders','ActiveWeeks'],ascending=False,kind='stable').head(pool_size).index.astype(str).tolist()
    # Same five reported SKUs as original statistical study; chosen pre-validation.
    top5=(popularity.loc[popularity.ActiveWeeks>=17]
           .sort_values(['Orders','ActiveWeeks'],ascending=False,kind='stable')
           .head(5).index.astype(str).tolist())
    assert set(top5).issubset(pool), 'Top-five evaluation SKUs missing from early-history training pool'
    raw['StockCode']=raw.StockCode.astype(str)
    wk=raw.loc[raw.StockCode.isin(pool)].groupby(['StockCode','WeekStart']).Quantity.sum().unstack('WeekStart',fill_value=0)
    wk=wk.reindex(index=pool,columns=weeks,fill_value=0)
    totals=raw.groupby('WeekStart').Quantity.sum().reindex(weeks,fill_value=0)
    names=(initial.loc[initial.StockCode.astype(str).isin(top5)].groupby('StockCode').Description
           .agg(lambda x:str(x.mode().iloc[0]) if len(x.mode()) else 'Unknown').to_dict())
    labels=['All products']+pool
    values=np.vstack([totals.to_numpy(float),wk.to_numpy(float)])
    result={'All products':'All product units',**{k:names.get(k,k) for k in pool}}
    return weeks,labels,values,top5,result


def features(history:np.ndarray, target_week:pd.Timestamp, horizon:int, aggregate:bool) -> np.ndarray:
    """All history values are known *at the forecast origin* (never beyond)."""
    past=np.asarray(history[-8:],float)
    if len(past)!=8:raise ValueError('At least eight full past weeks required')
    scale=max(1.,float(past.mean()))
    recent=past[-4:];older=past[:4]
    recent_mean=recent.mean();mean8=past.mean()
    vals=[float(horizon)]+list(past[::-1]/scale)+[
        float(recent_mean/scale),float(mean8/scale),float(recent.std()/scale),float(past.std()/scale),
        float((recent_mean-older.mean())/scale),float(np.count_nonzero(recent)/4),
        float(np.count_nonzero(past)/8),float(np.log1p(recent_mean)),float(np.log1p(mean8)),
        float(target_week.isocalendar().week),float(target_week.month),float(aggregate)]
    if len(vals)!=len(FEATURE_NAMES):raise AssertionError((len(vals),len(FEATURE_NAMES)))
    return np.array(vals,dtype='float32')


def panel_training(weeks, values:np.ndarray, origin:pd.Timestamp):
    """Training target date must strictly precede origin for *every* horizon."""
    end_idx=weeks.get_loc(origin)
    xs, ys, weights=[] , [], []
    # An anchor is a forecast origin in the historical training sample.
    # Require the full 4-week target block to have become observable already.
    for idx in range(8,end_idx-FORECAST_WEEKS+1):
        for k,series in enumerate(values):
            h=series[idx-8:idx]
            denom=max(1.,float(h.mean()))
            for ahead in range(1,FORECAST_WEEKS+1):
                target_idx=idx+ahead-1
                assert target_idx<end_idx
                xs.append(features(h,weeks[target_idx],ahead,k==0))
                # Dimensionless growth target permits pooled learning across
                # differently sized SKUs; transform back at forecast time.
                ys.append(min(20.,float(series[target_idx]/denom)))
                weights.append(2.0 if k==0 else 1.0)
    return np.vstack(xs),np.asarray(ys),np.asarray(weights)


def make_model(method):
    if method=='random_forest':
        return RandomForestRegressor(n_estimators=140,max_depth=9,min_samples_leaf=6,
                                     max_features=.8,random_state=SEED,n_jobs=4)
    if method=='xgboost':
        return XGBRegressor(n_estimators=170,max_depth=4,learning_rate=.055,
                            subsample=.9,colsample_bytree=.85,reg_lambda=12,
                            objective='reg:squarederror',tree_method='hist',
                            n_jobs=4,random_state=SEED)
    raise KeyError(method)


def predict_ml(model, values, weeks, origin:pd.Timestamp):
    idx=weeks.get_loc(origin)
    x=[];scales=[]
    for k,series in enumerate(values):
        recent=series[idx-8:idx]
        scales.append(max(1.,float(recent.mean())))
        for h in range(1,FORECAST_WEEKS+1):
            x.append(features(recent,weeks[idx+h-1],h,k==0))
    ratio=np.maximum(0.,model.predict(np.vstack(x)).reshape(len(values),FORECAST_WEEKS))
    return ratio * np.array(scales)[:,None]


def generate_predictions(weeks,values, origin):
    idx=weeks.get_loc(origin)
    truth=values[:,idx:idx+FORECAST_WEEKS]
    predictions={}
    for method in METHODS:
        predictions[method]=np.vstack([forecast(s[:idx],method) for s in values])
    train_x,train_y,weights=panel_training(weeks,values,origin)
    for method in ML_METHODS:
        model=make_model(method)
        model.fit(train_x,train_y,sample_weight=weights)
        predictions[method]=predict_ml(model,values, weeks,origin)
    return truth,predictions


def run(source:Path, output:Path=ROOT/'results', pool_size:int=POOL_SIZE):
    weeks,labels,values,top5,product_names=prepare_series(Path(source),pool_size)
    selected=['All products']+top5
    indices=[labels.index(k) for k in selected]
    validation=[]
    for origin in VALIDATION_ORIGINS:
        actual,pred=generate_predictions(weeks,values,origin)
        for label,i in zip(selected,indices):
            for method in ALL_METHODS:
                p=pred[method][i];y=actual[i]
                validation.append({'Series':label,'Product':product_names[label],
                                   'Origin':origin.date().isoformat(),'Method':method,
                                   'AbsoluteError':float(np.abs(y-p).sum()),
                                   'ActualTotal':float(y.sum()),'WAPE':float(wape(y,p))})
        print('Validated origin',origin.date(),flush=True)
    val=pd.DataFrame(validation)
    summary=(val.groupby(['Series','Method'],as_index=False)
             [['AbsoluteError','ActualTotal']].sum())
    summary['ValidationWAPE']=100*summary.AbsoluteError/summary.ActualTotal
    choices=[]
    for label in selected:
        rows=summary.loc[summary.Series==label].copy()
        rows['Priority']=rows.Method.map(ALL_METHODS.index)
        winner=rows.sort_values(['ValidationWAPE','Priority']).iloc[0]
        choices.append({'Series':label,'Product':product_names[label],
                        'SelectedByValidation':winner.Method,
                        'ValidationWAPE':float(winner.ValidationWAPE)})
    actual,pred=generate_predictions(weeks,values,TEST_ORIGIN)
    hold=[];rows=[];lookup={x['Series']:x['SelectedByValidation'] for x in choices}
    for label,i in zip(selected,indices):
        y=actual[i]
        for method in ALL_METHODS:
            p=pred[method][i]
            rows.append({'Series':label,'Product':product_names[label],
                         'Method':method,'ValidationWAPE':float(summary.loc[(summary.Series==label)&(summary.Method==method),'ValidationWAPE'].iloc[0]),
                         'HoldoutWAPE':float(wape(y,p)),
                         'ActualTotal':float(y.sum()),'ForecastTotal':float(p.sum()),
                         'SelectedByValidation':lookup[label]==method})
            for week,act,estimate in zip(weeks[weeks.get_loc(TEST_ORIGIN):weeks.get_loc(TEST_ORIGIN)+FORECAST_WEEKS],y,p):
                hold.append({'Series':label,'Product':product_names[label],
                             'WeekStart':week.date().isoformat(),'Method':method,
                             'ActualUnits':float(act),'ForecastUnits':float(estimate),
                             'SelectedByValidation':lookup[label]==method})
    output.mkdir(exist_ok=True,parents=True)
    val.to_csv(output/'ml_validation_folds.csv',index=False,float_format='%.5f')
    summary.to_csv(output/'ml_validation_scores.csv',index=False,float_format='%.5f')
    pd.DataFrame(choices).to_csv(output/'ml_selected_methods.csv',index=False,float_format='%.5f')
    pd.DataFrame(rows).to_csv(output/'ml_holdout_comparison.csv',index=False,float_format='%.5f')
    pd.DataFrame(hold).to_csv(output/'ml_holdout_weeks.csv',index=False,float_format='%.5f')
    relevant=pd.DataFrame(rows)
    baseline=relevant[(relevant.Series=='All products')&(relevant.Method=='four_week_mean')].iloc[0]
    selected_agg=relevant[(relevant.Series=='All products')&(relevant.SelectedByValidation)].iloc[0]
    report={
        'experiment':'Fixed-parameter pooled Random Forest and XGBoost vs three pre-existing statistical methods',
        'note':'Comparisons use historical, filtered observed unit sales—not true latent demand.',
        'training_pool':'Top 120 SKUs by distinct invoices from data strictly before 2011-05-30; >=12 active early weeks. Includes all-products as separate series.',
        'pool_size':len(labels)-1,'target':'dimensionless units / mean(previous 8 weekly units)',
        'features':list(FEATURE_NAMES),'algorithms':{
            'random_forest':'140 trees, depth 9, min leaf 6, max_features .8, fixed seed 42',
            'xgboost':'170 trees, depth 4, learning_rate .055, reg_lambda 12, subsample .9, colsample .85, fixed seed 42',
        },
        'forecast_strategy':'Direct horizon-aware four-week forecasts; only lagged data available at each origin, no actual holdout sales as features.',
        'validation_origins':[v.date().isoformat() for v in VALIDATION_ORIGINS],
        'test_origin':TEST_ORIGIN.date().isoformat(),
        'test_end_inclusive':'2011-12-04',
        'sku_selection':'Same original five top SKUs, chosen strictly before first validation; do not choose based on test.',
        'sku_list':top5,
        'selection_rule':'Lowest pooled absolute error / pooled actual units across five four-week validation folds per series. Same candidate pool for all six series. Preset ML hyperparameters, no holdout tuning.',
        'selected_aggregate_method':str(selected_agg.Method),
        'selected_aggregate_holdout_wape':round(float(selected_agg.HoldoutWAPE),3),
        'four_week_mean_holdout_wape':round(float(baseline.HoldoutWAPE),3),
        'all_product_comparison':relevant.loc[relevant.Series=='All products',
              ['Method','ValidationWAPE','HoldoutWAPE','ForecastTotal','SelectedByValidation']].to_dict('records'),
        'limitations':[
            'Only 52 complete weeks; one holiday season, no reliable annual seasonality.',
            'Data lacks stockouts, lost sales and promotions. Forecasted positive units sold are only an observed-sales proxy.',
            'SKUs were selected using early-history frequency; evaluation is for relatively active products, not all products.',
            'Pooled SKU panel shares the same calendar and is not independent customer data.',
            'No hyperparameter search; deeper ML tuning might produce different results, but must stay within historical folds.',
            'Reported performance is a single historical holdout, not proof of future reliability.'
        ]}
    (output/'ml_comparison_summary.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({k:report[k] for k in ('pool_size','selected_aggregate_method','selected_aggregate_holdout_wape','four_week_mean_holdout_wape','all_product_comparison')},indent=2),flush=True)
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=ROOT/'data/raw/Online Retail.csv');ap.add_argument('--pool-size',type=int,default=POOL_SIZE)
    a=ap.parse_args();run(a.source,pool_size=a.pool_size)
