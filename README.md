# Carbon Cycle Prediction Using Meteorological Data Based on XGBoost

## Overview

This project builds a carbon flux (Net Ecosystem Exchange, NEE) prediction model using XGBoost regression on meteorological NetCDF data for Ya'an, China (latitude 30.0, longitude 103.0). The pipeline extracts atmospheric variables at the 1000 hPa pressure level, engineers time-based cyclic features and lag features, and trains an XGBoost regressor to predict NEE.

> **Note:** The current implementation uses **synthetic NEE labels** generated from simplified GPP and ecosystem respiration (Reco) formulas. These labels are derived from the same meteorological variables used as model input features (temperature, humidity, solar radiation proxy). Consequently, model performance metrics do not reflect real-world predictive capability. To use this pipeline with real carbon flux data, replace the synthetic label generation in `Preprocessing.py` with observed NEE measurements (e.g., from FLUXNET or eddy covariance towers).

## Technical Path

### Data Processing (`Preprocessing.py`)

1. Load all `.nc` files from the `Data/` directory at the project root, skipping corrupted files automatically.
2. Combine datasets along the time dimension using `xarray.open_mfdataset`.
3. Select the nearest grid point to Ya'an (lat=30.0, lon=103.0).
4. Extract variables at the 1000 hPa pressure level.
5. Convert to a tabular DataFrame and drop unused columns (`number`, `ciwc`, `cswc`, `cc`, `clwc`).
6. Engineer features:
   - Cyclic time features: `hour_sin`, `hour_cos`, `doy_sin`, `doy_cos` (sine/cosine encoding of hour-of-day and day-of-year).
   - Wind speed: `wind_speed = sqrt(u^2 + v^2)`.
   - Lag features: `t_lag1`, `t_lag2`, `r_lag1`, `r_lag2`, `wind_lag1`, `wind_lag2` (1- and 2-step backward shifts).
7. Generate synthetic NEE labels:
   - GPP = 10 * light * exp(-((T - 25)/10)^2) * RH * lat_factor
   - Reco = 2 * exp(0.08 * T) * (1 + 0.3 * (1 - lat_factor))
   - NEE = Reco - GPP + Gaussian noise (mean=0, std=0.5, seed=42)
8. Drop rows with NaN values (from lag feature generation).

### Dataset Split (`Dataset.py`)

- Features: `t`, `r`, `u`, `v`, `wind_speed`, `latitude`, `longitude`, `hour_sin`, `hour_cos`, `doy_sin`, `doy_cos`, `t_lag1`, `t_lag2`, `r_lag1`, `r_lag2`, `wind_lag1`, `wind_lag2`
- Target: `NEE_sim` (synthetic)
- Temporal split: train on data up to and including 2024, test on 2025 data only.
- Lag features point strictly backwards in time to prevent future information leakage.

### Model (`Model.py`)

- Algorithm: XGBoost (`XGBRegressor`)
- Hyperparameters:
  - `n_estimators=500`
  - `max_depth=6`
  - `learning_rate=0.05`
  - `subsample=0.8`
  - `colsample_bytree=0.8`
  - `tree_method="hist"`
  - `random_state=42`
- The trained model is saved to `xgb_model.json`.

### Evaluation

Model performance is evaluated on the 2025 test set using:
- R² (coefficient of determination)
- RMSE (root mean squared error)
- MAE (mean absolute error)

All random seeds are fixed (seed=42) so results are reproducible given the same input data.

### Visualization (`Visualization.py`)

Four plots are generated:
1. Time series comparison of true vs. predicted NEE on the test set.
2. Diurnal cycle comparison (hourly mean of true vs. predicted NEE).
3. XGBoost feature importance.
4. Prediction error distribution histogram.

## How to Run

### Prerequisites

Install dependencies:

```bash
pip install -r requirements.txt
```

### Data Preparation

Place ERA5 or compatible NetCDF (`.nc`) files in a `Data/` directory at the project root:

```
project-root/
├── Data/
│   ├── file1.nc
│── ├── file2.nc
│   └── ...
├── src/
│   ├── Preprocessing.py
│   ├── Dataset.py
│   ├── Model.py
│   └── Visualization.py
├── requirements.txt
└── README.md
```

### Execution

Run the pipeline from the `src/` directory in the following order:

```bash
cd src
python Preprocessing.py
python Model.py
python Visualization.py
```

- `Preprocessing.py` loads and processes the NetCDF data, generates features and synthetic labels.
- `Model.py` imports the preprocessed data (triggers `Preprocessing` and `Dataset` modules), trains the XGBoost model, and prints evaluation metrics (RMSE, R², MAE).
- `Visualization.py` imports the trained model and generates the four plots.

## Project Structure

```
├── src/
│   ├── Preprocessing.py    # Data loading, feature engineering, synthetic NEE generation
│   ├── Dataset.py          # Feature selection and temporal train/test split
│   ├── Model.py            # XGBoost training and evaluation
│   └── Visualization.py    # Plotting (time series, diurnal cycle, feature importance, errors)
├── requirements.txt
├── LICENSE
└── README.md
```
