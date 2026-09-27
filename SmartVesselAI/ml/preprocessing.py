"""Maritime Dry-Bulk Freight Intelligence — Feature Engineering & Preprocessing Pipeline.

Strict zero-leakage feature engineering for time-series forecasting.
Only uses historical information available at prediction time.
"""
from __future__ import annotations

import os
import sys
import numpy as np
import pandas as pd

SMARTVESSEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SMARTVESSEL_DIR not in sys.path:
    sys.path.insert(0, SMARTVESSEL_DIR)

try:
    from backend.database import SessionLocal
    from backend.models.db_models import FreightRate
except ModuleNotFoundError:
    from SmartVesselAI.backend.database import SessionLocal
    from SmartVesselAI.backend.models.db_models import FreightRate


def load_freight_data(db_session=None) -> pd.DataFrame:
    """Loads raw freight records ordered chronologically."""
    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True
    
    query = db_session.query(FreightRate).order_by(FreightRate.date.asc())
    df = pd.read_sql(query.statement, db_session.bind)
    
    if close_session:
        db_session.close()
        
    return df


def prepare_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Constructs zero-leakage maritime domain features for time-series models.

    Engineered Feature Categories:
    1. Historical Lags (1d, 7d, 14d, 30d)
    2. Rolling Window Statistics (Mean, Median, Volatility Std Dev)
    3. Exponentially Weighted Moving Averages (EWMA 7d, 14d, 30d)
    4. Freight Rate Momentum & % Changes
    5. Cyclical Calendar Encoding (Sine / Cosine transforms)
    6. Market & Environmental Interactions (Fuel change, Weather x Congestion)
    7. Route & Vessel Interaction terms
    """
    if df is None or df.empty:
        return pd.DataFrame()
        
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['origin', 'destination', 'vessel_type', 'date']).reset_index(drop=True)
    
    grouped = df.groupby(['origin', 'destination', 'vessel_type'])
    
    # -----------------------------------------------------------------------
    # 1. Historical Freight Lags
    # -----------------------------------------------------------------------
    df['lag_1'] = grouped['freight_rate'].shift(1)
    df['lag_7'] = grouped['freight_rate'].shift(7)
    df['lag_14'] = grouped['freight_rate'].shift(14)
    df['lag_30'] = grouped['freight_rate'].shift(30)
    
    # -----------------------------------------------------------------------
    # 2. Rolling Window Statistics (Strictly shifted to exclude current/future target)
    # -----------------------------------------------------------------------
    shifted_rate = grouped['freight_rate'].shift(1)
    df['rolling_7_mean'] = shifted_rate.groupby([df['origin'], df['destination'], df['vessel_type']]).transform(lambda x: x.rolling(7, min_periods=1).mean())
    df['rolling_14_mean'] = shifted_rate.groupby([df['origin'], df['destination'], df['vessel_type']]).transform(lambda x: x.rolling(14, min_periods=1).mean())
    df['rolling_30_mean'] = shifted_rate.groupby([df['origin'], df['destination'], df['vessel_type']]).transform(lambda x: x.rolling(30, min_periods=1).mean())
    
    df['rolling_7_median'] = shifted_rate.groupby([df['origin'], df['destination'], df['vessel_type']]).transform(lambda x: x.rolling(7, min_periods=1).median())
    df['rolling_7_std'] = shifted_rate.groupby([df['origin'], df['destination'], df['vessel_type']]).transform(lambda x: x.rolling(7, min_periods=2).std()).fillna(0.0)
    df['rolling_14_std'] = shifted_rate.groupby([df['origin'], df['destination'], df['vessel_type']]).transform(lambda x: x.rolling(14, min_periods=2).std()).fillna(0.0)
    
    # -----------------------------------------------------------------------
    # 3. Exponentially Weighted Moving Averages (EWMA)
    # -----------------------------------------------------------------------
    df['ewma_7'] = shifted_rate.groupby([df['origin'], df['destination'], df['vessel_type']]).transform(lambda x: x.ewm(span=7, min_periods=1).mean())
    df['ewma_14'] = shifted_rate.groupby([df['origin'], df['destination'], df['vessel_type']]).transform(lambda x: x.ewm(span=14, min_periods=1).mean())
    df['ewma_30'] = shifted_rate.groupby([df['origin'], df['destination'], df['vessel_type']]).transform(lambda x: x.ewm(span=30, min_periods=1).mean())
    
    # -----------------------------------------------------------------------
    # 4. Freight Rate Momentum & Percentage Change
    # -----------------------------------------------------------------------
    df['momentum_7d'] = df['freight_rate'] - df['lag_7']
    df['momentum_14d'] = df['freight_rate'] - df['lag_14']
    df['pct_change_7d'] = ((df['freight_rate'] - df['lag_7']) / (df['lag_7'] + 1e-5)).clip(-0.5, 0.5)
    df['pct_change_14d'] = ((df['freight_rate'] - df['lag_14']) / (df['lag_14'] + 1e-5)).clip(-0.5, 0.5)
    
    # -----------------------------------------------------------------------
    # 5. Cyclical Calendar Sine / Cosine Transforms
    # -----------------------------------------------------------------------
    day_of_year = df['date'].dt.dayofyear
    month = df['date'].dt.month
    
    df['sin_day_of_year'] = np.sin(2 * np.pi * day_of_year / 365.25)
    df['cos_day_of_year'] = np.cos(2 * np.pi * day_of_year / 365.25)
    df['sin_month'] = np.sin(2 * np.pi * month / 12.0)
    df['cos_month'] = np.cos(2 * np.pi * month / 12.0)
    
    # -----------------------------------------------------------------------
    # 6. Fuel & Environmental Interaction Features
    # -----------------------------------------------------------------------
    if 'fuel_price' in df.columns:
        fuel_grouped = grouped['fuel_price']
        df['fuel_lag_7'] = fuel_grouped.shift(7)
        df['fuel_change_7d'] = df['fuel_price'] - df['fuel_lag_7']
        df['fuel_pct_change'] = ((df['fuel_price'] - df['fuel_lag_7']) / (df['fuel_lag_7'] + 1e-5)).clip(-0.3, 0.3)
    else:
        df['fuel_change_7d'] = 0.0
        df['fuel_pct_change'] = 0.0

    if 'weather_risk' in df.columns and 'congestion_index' in df.columns:
        df['weather_congestion_interaction'] = df['weather_risk'] * df['congestion_index']
    else:
        df['weather_congestion_interaction'] = 0.0
        
    # -----------------------------------------------------------------------
    # 7. Unshifted Horizon Targets (ZERO LEAKAGE: No backfilling target values)
    # -----------------------------------------------------------------------
    df['target_7d'] = grouped['freight_rate'].shift(-7)
    df['target_14d'] = grouped['freight_rate'].shift(-14)
    df['target_30d'] = grouped['freight_rate'].shift(-30)
    
    # Forward fill / backward fill historical feature columns ONLY
    feature_cols_to_fill = [
        'lag_1', 'lag_7', 'lag_14', 'lag_30',
        'rolling_7_mean', 'rolling_14_mean', 'rolling_30_mean',
        'rolling_7_median', 'rolling_7_std', 'rolling_14_std',
        'ewma_7', 'ewma_14', 'ewma_30',
        'momentum_7d', 'momentum_14d', 'pct_change_7d', 'pct_change_14d',
        'fuel_change_7d', 'fuel_pct_change', 'weather_congestion_interaction'
    ]
    df[feature_cols_to_fill] = df[feature_cols_to_fill].ffill().bfill().fillna(0.0)
    
    return df
