# 基于气象数据的碳循环预测模型 (XGBoost)

## 概述

本项目使用 XGBoost 回归模型，基于气象 NetCDF 数据（四川雅安，纬度 30.0，经度 103.0）构建净碳通量交换（NEE）预测模型。流程从 1000 hPa 气压层提取大气变量，构造周期性时间特征和滞后特征，训练 XGBoost 回归器预测 NEE。

> **注意：** 当前实现使用**合成 NEE 标签**，由简化的总初级生产力（GPP）和生态系统呼吸（Reco）公式生成。这些标签的生成依赖于与模型输入特征相同的气象变量（温度、湿度、辐射代理），因此模型性能指标不能反映真实预测能力。如需用于实际碳通量预测，请将 `Preprocessing.py` 中的合成标签生成部分替换为实测 NEE 数据（如 FLUXNET 或涡度通量塔数据）。

## 技术路径

### 数据处理 (`Preprocessing.py`)

1. 从项目根目录下的 `Data/` 文件夹加载所有 `.nc` 文件，自动跳过损坏文件。
2. 使用 `xarray.open_mfdataset` 沿时间维度合并数据集。
3. 选取最接近雅安（纬度=30.0，经度=103.0）的网格点。
4. 提取 1000 hPa 气压层的变量。
5. 转换为 DataFrame 格式，删除无用列（`number`、`ciwc`、`cswc`、`cc`、`clwc`）。
6. 特征工程：
   - 周期性时间特征：`hour_sin`、`hour_cos`、`doy_sin`、`doy_cos`（小时和年序日的正余弦编码）。
   - 风速：`wind_speed = sqrt(u^2 + v^2)`。
   - 滞后特征：`t_lag1`、`t_lag2`、`r_lag1`、`r_lag2`、`wind_lag1`、`wind_lag2`（1 步和 2 步后向位移）。
7. 生成合成 NEE 标签：
   - GPP = 10 * light * exp(-((T - 25)/10)^2) * RH * lat_factor
   - Reco = 2 * exp(0.08 * T) * (1 + 0.3 * (1 - lat_factor))
   - NEE = Reco - GPP + 高斯噪声（均值=0，标准差=0.5，种子=42）
8. 删除含 NaN 的行（由滞后特征生成产生）。

### 数据集划分 (`Dataset.py`)

- 特征：`t`、`r`、`u`、`v`、`wind_speed`、`latitude`、`longitude`、`hour_sin`、`hour_cos`、`doy_sin`、`doy_cos`、`t_lag1`、`t_lag2`、`r_lag1`、`r_lag2`、`wind_lag1`、`wind_lag2`
- 目标：`NEE_sim`（合成）
- 时间划分：训练集为 2024 年及之前的数据，测试集为 2025 年的数据。
- 滞后特征严格指向过去时间，防止未来信息泄漏。

### 模型 (`Model.py`)

- 算法：XGBoost（`XGBRegressor`）
- 超参数：
  - `n_estimators=500`
  - `max_depth=6`
  - `learning_rate=0.05`
  - `subsample=0.8`
  - `colsample_bytree=0.8`
  - `tree_method="hist"`
  - `random_state=42`
- 训练后的模型保存为 `xgb_model.json`。

### 评估

在 2025 年测试集上使用以下指标评估模型性能：
- R²（决定系数）
- RMSE（均方根误差）
- MAE（平均绝对误差）

所有随机种子固定为 42，在相同输入数据下结果可复现。

### 可视化 (`Visualization.py`)

生成四张图：
1. 测试集真实值与预测值的时间序列对比。
2. 日变化周期对比（真实值与预测值的逐小时均值）。
3. XGBoost 特征重要性。
4. 预测误差分布直方图。

## 运行方式

### 环境依赖

安装依赖：

```bash
pip install -r requirements.txt
```

### 数据准备

将 ERA5 或兼容格式的 NetCDF（`.nc`）文件放入项目根目录下的 `Data/` 文件夹：

```
项目根目录/
├── Data/
│   ├── file1.nc
│   ├── file2.nc
│   └── ...
├── src/
│   ├── Preprocessing.py
│   ├── Dataset.py
│   ├── Model.py
│   └── Visualization.py
├── requirements.txt
└── README.md
```

### 执行

按以下顺序从 `src/` 目录运行流水线：

```bash
cd src
python Preprocessing.py
python Model.py
python Visualization.py
```

- `Preprocessing.py`：加载和处理 NetCDF 数据，生成特征和合成标签。
- `Model.py`：导入预处理数据（触发 `Preprocessing` 和 `Dataset` 模块），训练 XGBoost 模型，输出评估指标（RMSE、R²、MAE）。
- `Visualization.py`：导入训练好的模型，生成四张可视化图表。

## 项目结构

```
├── src/
│   ├── Preprocessing.py    # 数据加载、特征工程、合成 NEE 生成
│   ├── Dataset.py          # 特征选择和时间序列训练/测试集划分
│   ├── Model.py            # XGBoost 训练与评估
│   └── Visualization.py    # 可视化（时间序列、日变化、特征重要性、误差分布）
├── requirements.txt
├── LICENSE
└── README.md
```
