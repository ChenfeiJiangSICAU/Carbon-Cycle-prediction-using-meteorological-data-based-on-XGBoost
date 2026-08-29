from Preprocessing import df


features = [
    "t", "r", "u", "v", "wind_speed",
    "latitude", "longitude",
    "hour_sin", "hour_cos",
    "doy_sin", "doy_cos",
    "t_lag1", "t_lag2",
    "r_lag1", "r_lag2",
    "wind_lag1", "wind_lag2"
]

X = df[features]
y = df["NEE_sim"]


# Temporal split: train on everything up to 2024, test on 2025 only.
# Lag features point strictly backwards in time, so no future information
# leaks into the training rows.
years = df["valid_time"].dt.year
train_idx = years <= 2024
test_idx = years == 2025

n_train = int(train_idx.sum())
n_test = int(test_idx.sum())
if n_train == 0:
    raise ValueError("训练集为空：数据中没有 2024 年及之前的样本。")
if n_test == 0:
    raise ValueError(
        "测试集为空：数据中没有 2025 年的样本，无法评估模型。"
        f"当前数据覆盖 {int(years.min())}–{int(years.max())} 年，"
        "请检查数据时间范围。"
    )

unused_years = sorted(
    int(year) for year in set(years) if int(year) > 2025
)
if unused_years:
    print(
        "Warning: 以下年份既不属于训练集也不属于测试集，将被忽略: "
        + ", ".join(str(year) for year in unused_years)
    )


X_train, X_test = X[train_idx], X[test_idx]
y_train, y_test = y[train_idx], y[test_idx]

print("Split successfully done")

