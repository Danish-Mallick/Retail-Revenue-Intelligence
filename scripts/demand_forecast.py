"""Historical 4-week SKU-level sold-unit forecast, backtested without data leakage.

'Observed unit sales' is a proxy, NOT unconstrained true demand: stockouts and
returns/cancellations aren't present in the filtered retail extract. Model
selection ends before a final untouched November 2011 holdout.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze import ROOT, fix_dates, load_extract

FIRST_WEEK = pd.Timestamp('2010-12-06')
LAST_WEEK = pd.Timestamp('2011-11-28')
VALIDATION_ORIGINS = pd.to_datetime(['2011-05-30','2011-06-27','2011-07-25','2011-08-22','2011-09-19'])
TEST_ORIGIN = pd.Timestamp('2011-11-07')
FORECAST_WEEKS = 4
METHODS = ('four_week_mean','four_week_repeat','eight_week_damped_trend')


def forecast(train: np.ndarray, method: str, horizon: int = FORECAST_WEEKS) -> np.ndarray:
    train = np.asarray(train, dtype=float)
    if len(train) < 8: raise ValueError('Need at least 8 complete weeks of history')
    if method == 'four_week_mean':
        result = np.repeat(np.mean(train[-4:]), horizon)
    elif method == 'four_week_repeat':
        result = np.resize(train[-4:], horizon).astype(float)
    elif method == 'eight_week_damped_trend':
        # Limit runaway forecasts from one short, noisy historical series.
        y = train[-8:]
        slope = float(np.polyfit(np.arange(8), y, 1)[0])
        slope = np.clip(slope, -0.18 * max(1, y.mean()), 0.18 * max(1, y.mean()))
        level = float(np.mean(y[-4:]))
        result = level + slope * np.cumsum(0.65 ** np.arange(1, horizon+1))
    else: raise KeyError(method)
    return np.maximum(result, 0.)


def wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    den = np.sum(np.abs(actual))
    if den == 0: return np.nan
    return 100 * np.sum(np.abs(actual-predicted)) / den


def run(source: Path, output: Path = ROOT / 'results') -> dict:
    raw = load_extract(source)
    _, corrected, _ = fix_dates(raw)
    raw['WeekStart'] = corrected.dt.to_period('W-SUN').dt.start_time
    all_weeks = pd.date_range(FIRST_WEEK,LAST_WEEK,freq='W-MON')
    # Selection sees only the initial period. No best-selling status inferred
    # from the evaluation months, which would bias the backtest.
    initial = raw.loc[(raw.WeekStart >= FIRST_WEEK) & (raw.WeekStart < VALIDATION_ORIGINS[0])]
    popularity = initial.groupby('StockCode').agg(Orders=('InvoiceNo','nunique'),
                                     ActiveWeeks=('WeekStart','nunique'))
    selected = (popularity.loc[popularity.ActiveWeeks >= 17]
                .sort_values(['Orders','ActiveWeeks'],ascending=False).head(5).index.tolist())
    names = (initial.loc[initial.StockCode.isin(selected)].groupby('StockCode').Description
             .agg(lambda s: s.mode().iloc[0] if len(s.mode()) else 'Unknown').to_dict())
    series = {'All products':raw.groupby('WeekStart').Quantity.sum().reindex(all_weeks,fill_value=0)}
    for stock in selected:
        series[str(stock)] = (raw.loc[raw.StockCode==stock].groupby('WeekStart').Quantity.sum()
                              .reindex(all_weeks,fill_value=0))
    validation = []
    evaluation = []
    plotted = []
    winners = []
    for label,s in series.items():
        for origin in VALIDATION_ORIGINS:
            prior=s.loc[s.index<origin].to_numpy(float)
            actual=s.loc[(s.index>=origin)&(s.index<origin+pd.Timedelta(weeks=FORECAST_WEEKS))].to_numpy(float)
            assert len(actual)==FORECAST_WEEKS and len(prior)>=8
            for model in METHODS:
                pred=forecast(prior,model)
                validation.append(dict(Series=label,Origin=origin.date().isoformat(),Method=model,
                                       AbsoluteError=float(np.abs(actual-pred).sum()),
                                       ActualTotal=float(np.abs(actual).sum()),
                                       WAPE=float(wape(actual,pred))))
        v=pd.DataFrame(x for x in validation if x['Series']==label)
        agg=v.groupby('Method',as_index=False)[['AbsoluteError','ActualTotal']].sum()
        agg['ValidationWAPE']=100*agg.AbsoluteError/agg.ActualTotal
        # deterministic simple-model tie-break
        winner=sorted(agg.to_dict('records'),key=lambda x:(round(x['ValidationWAPE'],8),METHODS.index(x['Method'])))[0]
        winners.append(dict(Series=label,Product=names.get(label,'All product units'),
                            Method=winner['Method'],ValidationWAPE=round(winner['ValidationWAPE'],2)))
        prior=s.loc[s.index<TEST_ORIGIN].to_numpy(float)
        test=s.loc[(s.index>=TEST_ORIGIN)&(s.index<TEST_ORIGIN+pd.Timedelta(weeks=FORECAST_WEEKS))]
        assert len(test)==FORECAST_WEEKS
        p=forecast(prior,winner['Method'])
        naive=forecast(prior,'four_week_mean')
        for week,actual,estimate,base in zip(test.index,test.to_numpy(float),p,naive):
            evaluation.append(dict(Series=label,Product=names.get(label,'All product units'),
                                    WeekStart=week.date().isoformat(),ActualUnits=int(actual),
                                    ForecastUnits=round(float(estimate),1),
                                    BaselineUnits=round(float(base),1)))
        plotted.append(dict(Series=label,Product=names.get(label,'All product units'),
                            SelectedMethod=winner['Method'],
                            HoldoutWAPE=round(wape(test.to_numpy(float),p),2),
                            BaselineHoldoutWAPE=round(wape(test.to_numpy(float),naive),2),
                            ActualTotal=int(test.sum()),ForecastTotal=round(float(p.sum()),1),
                            BaselineForecastTotal=round(float(naive.sum()),1)))
    output.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(validation).to_csv(output/'forecast_validation_folds.csv',index=False)
    pd.DataFrame(winners).to_csv(output/'forecast_model_selection.csv',index=False)
    pd.DataFrame(evaluation).to_csv(output/'forecast_holdout_weeks.csv',index=False)
    pd.DataFrame(plotted).to_csv(output/'forecast_evaluation.csv',index=False)
    # Chart series is non-sensitive grouped units, ideal for a Power BI forecast page.
    history=pd.DataFrame({'WeekStart':all_weeks})
    for lab,s in series.items(): history[lab] = s.values
    history.to_csv(output/'forecast_weekly_history.csv',index=False)
    summary={
        'description':'Historical four-week forecasting experiment using positive recorded units, not total true demand',
        'first_full_week':str(FIRST_WEEK.date()),'last_full_week':str(LAST_WEEK.date()),
        'excluded':'2010-11-29 (partial first week); 2011-12-05 (partial final week)',
        'observed_zero_week':'2010-12-27 (no observed transactions; assumed zero observed units, not proof of zero true demand)',
        'model_selection_end':'2011-10-16',
        'final_holdout':'2011-11-07 through 2011-12-04 (four complete weeks)',
        'gap':'Oct 17 to Nov 6 left out of tuning, included in final model training',
        'forecast_horizon_weeks':FORECAST_WEEKS,
        'sku_selection':'top five by distinct invoices during initial weeks ending 2011-05-29; >=17 active weeks',
        'sku_list':selected,
        'results':plotted,
        'caveat':'One historical year, changing sales levels, unknown stockouts and promotions; validation is illustrative, not production-grade.'}
    (output/'forecast_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    return summary

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',default=str(ROOT/'data/raw/Online Retail.csv'))
    args=parser.parse_args()
    s=run(Path(args.source))
    print(json.dumps(s,indent=2))
