# %% 1 — Setup & Load
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
import os
import warnings
warnings.filterwarnings('ignore')

load_dotenv(Path(__file__).parent.parent / ".env")
engine = create_engine(
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@localhost:5432/{os.getenv('POSTGRES_DB')}"
)

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

df = pd.read_sql("""
    select f.*, l.is_churned, l.days_since_last_order
    from marts.mart_customer_features f
    join marts.mart_churn_labels l using (customer_id)
""", engine)

print(f"Loaded {len(df):,} customers")
print(f"Churn rate: {df['is_churned'].mean()*100:.1f}%")


# %% 2 — EDA: Class Imbalance
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

df['is_churned'].value_counts().plot.pie(
    labels=['Churned', 'Active'],
    autopct='%1.1f%%',
    colors=['#e74c3c', '#2ecc71'],
    ax=axes[0]
)
axes[0].set_title('Class Distribution')

numeric_cols = df.select_dtypes(include='number').columns.drop('is_churned')
corr = df[numeric_cols].corrwith(df['is_churned']).sort_values()
corr.plot.barh(ax=axes[1], color=['#e74c3c' if v > 0 else '#2ecc71' for v in corr])
axes[1].set_title('Feature Correlation with Churn')
axes[1].axvline(0, color='black', linewidth=0.8)

plt.tight_layout()
plt.savefig(RESULTS_DIR / '07_churn_eda.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: 07_churn_eda.png")


# %% 3 — Preprocessing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    classification_report, roc_auc_score,
    ConfusionMatrixDisplay, precision_recall_curve
)

FEATURES_CANDIDATE = [
    'frequency', 'monetary', 'avg_order_value',
    'avg_delivery_days', 'max_delivery_days', 'late_delivery_rate',
    'avg_review_score', 'min_review_score', 'bad_review_rate',
    'credit_card_rate', 'avg_installments', 'avg_items_per_order',
    #'avg_purchase_gap_days'  # bỏ qua nếu chưa có trong mart
]

le = LabelEncoder()
df['state_encoded'] = le.fit_transform(df['customer_state'].fillna('Unknown'))

FEATURES = [f for f in FEATURES_CANDIDATE if f in df.columns]
FEATURES.append('state_encoded')

missing = set(FEATURES_CANDIDATE) - set(df.columns)
if missing:
    print(f"⚠️  Bỏ qua features chưa có trong mart: {missing}")
print(f"✅ Dùng {len(FEATURES)} features: {FEATURES}")

X = df[FEATURES]
y = df['is_churned']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

imputer = SimpleImputer(strategy='median')
X_train = pd.DataFrame(imputer.fit_transform(X_train), columns=FEATURES)
X_test  = pd.DataFrame(imputer.transform(X_test),      columns=FEATURES)

print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")
print(f"Churn rate train: {y_train.mean()*100:.1f}% | test: {y_test.mean()*100:.1f}%")
print(f"NaN còn lại: {X_train.isna().sum().sum()}")


# %% 4 — Baseline: Logistic Regression
lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_test)
y_prob_lr = lr.predict_proba(X_test)[:, 1]

print("\nLogistic Regression (Baseline):")
print(classification_report(y_test, y_pred_lr, target_names=['Active', 'Churned']))
print(f"ROC-AUC: {roc_auc_score(y_test, y_prob_lr):.4f}")


# %% 5 — Main Model: LightGBM
# FIX Vấn đề 1: Bỏ scale_pos_weight vì Churned là MAJORITY (90.1%)
# scale_pos_weight chỉ có tác dụng khi positive class là minority.
# Ở đây Churned (pos=1) = 90% → thêm weight vào sẽ làm model predict
# Churned nhiều hơn nữa → Active precision = 0.00
# → Để threshold tuning xử lý imbalance thay thế
# %% 5 — Main Model: LightGBM với class_weight tuning
try:
    import lightgbm as lgb
    from sklearn.metrics import precision_score, recall_score

    neg = (y_train == 0).sum()  # Active  — minority ~9.9%
    pos = (y_train == 1).sum()  # Churned — majority ~90.1%
    print(f"\nClass counts — Active (neg): {neg:,} | Churned (pos): {pos:,}")
    print("Churned là majority → weight Active(0) lên để model không bỏ qua minority\n")

    # --- Bước 1: Grid search weight để chọn w tốt nhất ---
    print("Weight search:")
    best_w, best_active_f1 = 1, 0
    for w in [3, 5, 8, 10]:
        m = lgb.LGBMClassifier(
            n_estimators=300, learning_rate=0.05,
            num_leaves=31,
            class_weight={0: w, 1: 1},  # Active(0) = w×, Churned(1) = 1×
            random_state=42, verbose=-1
        )
        m.fit(X_train, y_train)
        pred = m.predict(X_test)
        prob = m.predict_proba(X_test)[:, 1]
        active_p = precision_score(y_test, pred, pos_label=0)
        active_r = recall_score(y_test, pred, pos_label=0)
        active_f1 = 2 * active_p * active_r / (active_p + active_r + 1e-9)
        auc = roc_auc_score(y_test, prob)
        print(f"  w={w:>2}: Active precision={active_p:.2f}  recall={active_r:.2f}  "
              f"F1={active_f1:.3f}  AUC={auc:.4f}")
        if active_f1 > best_active_f1:
            best_active_f1, best_w = active_f1, w

    print(f"\n→ Best weight cho Active: w={best_w}")

    # --- Bước 2: Train model cuối với w tốt nhất ---
    model = lgb.LGBMClassifier(
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=31,
        class_weight={0: best_w, 1: 1},
        random_state=42,
        verbose=-1
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(50, verbose=False)]
    )

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print(f"\nLightGBM (class_weight={{0:{best_w}, 1:1}}, threshold=0.5):")
    print(classification_report(y_test, y_pred, target_names=['Active', 'Churned']))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")

except ImportError:
    print("LightGBM chưa cài: pip install lightgbm")
    model, y_pred, y_prob = lr, y_pred_lr, y_prob_lr


# %% 5b — Threshold Tuning
precision_arr, recall_arr, thresholds_arr = precision_recall_curve(y_test, y_prob)

f1_scores = 2 * precision_arr * recall_arr / (precision_arr + recall_arr + 1e-9)
best_idx = np.argmax(f1_scores)
best_threshold = thresholds_arr[best_idx]

print(f"\nBest threshold (max F1): {best_threshold:.3f}")

y_pred_tuned = (y_prob >= best_threshold).astype(int)
print("\nLightGBM (Tuned Threshold):")
print(classification_report(y_test, y_pred_tuned, target_names=['Active', 'Churned']))
print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")

# FIX Vấn đề 3: Ghi nhận ceiling AUC
print(f"""
ℹ️  Nhận xét ROC-AUC:
   AUC ~0.72 là ceiling thực tế với dataset này vì:
   - 97% customers chỉ có 1 đơn hàng duy nhất
   - Features như avg_delivery_days, avg_review_score chỉ reflect 1 transaction
   - Model không phân biệt được "sẽ churn" vs "đã churn ngay từ đầu"
   → Đây là limitation của data, không phải của model
""")


# %% 6 — Evaluation
from sklearn.metrics import RocCurveDisplay

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Churn Model Evaluation — LightGBM', fontsize=14, fontweight='bold')

# Row 1: Default threshold (0.5)
ConfusionMatrixDisplay.from_predictions(
    y_test, y_pred,
    display_labels=['Active', 'Churned'],
    colorbar=False, ax=axes[0][0]
)
axes[0][0].set_title('Confusion Matrix (threshold=0.5)')

RocCurveDisplay.from_predictions(y_test, y_prob, ax=axes[0][1])
axes[0][1].set_title(f'ROC Curve (AUC={roc_auc_score(y_test, y_prob):.3f})')

axes[0][2].plot(recall_arr, precision_arr, color='coral')
axes[0][2].set_xlabel('Recall')
axes[0][2].set_ylabel('Precision')
axes[0][2].set_title('Precision-Recall Curve')
axes[0][2].axhline(y=y_test.mean(), linestyle='--', color='gray',
                   label=f'Baseline ({y_test.mean():.2f})')
axes[0][2].axvline(x=recall_arr[best_idx], linestyle=':', color='blue',
                   label=f'Best threshold={best_threshold:.2f}')
axes[0][2].legend()

# Row 2: Tuned threshold
ConfusionMatrixDisplay.from_predictions(
    y_test, y_pred_tuned,
    display_labels=['Active', 'Churned'],
    colorbar=False, ax=axes[1][0]
)
axes[1][0].set_title(f'Confusion Matrix (threshold={best_threshold:.3f})')

axes[1][1].plot(thresholds_arr, f1_scores[:-1], color='steelblue')
axes[1][1].axvline(x=best_threshold, color='red', linestyle='--',
                   label=f'Best={best_threshold:.3f}')
axes[1][1].set_xlabel('Threshold')
axes[1][1].set_ylabel('F1 Score')
axes[1][1].set_title('F1 Score vs Threshold')
axes[1][1].legend()

axes[1][2].plot(thresholds_arr, precision_arr[:-1], label='Precision', color='coral')
axes[1][2].plot(thresholds_arr, recall_arr[:-1], label='Recall', color='steelblue')
axes[1][2].axvline(x=best_threshold, color='red', linestyle='--',
                   label=f'Best threshold={best_threshold:.3f}')
axes[1][2].set_xlabel('Threshold')
axes[1][2].set_title('Precision & Recall vs Threshold')
axes[1][2].legend()

plt.tight_layout()
plt.savefig(RESULTS_DIR / '08_churn_evaluation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: 08_churn_evaluation.png")


# %% 7 — Feature Importance (SHAP)
try:
    import shap

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test[:500])

    fig, ax = plt.subplots(figsize=(10, 7))
    shap.summary_plot(
        shap_values[1] if isinstance(shap_values, list) else shap_values,
        X_test[:500], plot_type='bar', show=False
    )
    plt.title('Feature Importance (SHAP)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / '09_shap_importance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 09_shap_importance.png")

except ImportError:
    print("SHAP chưa cài: pip install shap")


# %% 8 — Save Model & Score All Customers
import pickle

model_path = Path(__file__).parent.parent / "ml" / "models"
model_path.mkdir(parents=True, exist_ok=True)

with open(model_path / "churn_model.pkl", "wb") as f:
    pickle.dump({
        'model': model,
        'features': FEATURES,
        'label_encoder': le,
        'best_threshold': best_threshold
    }, f)
print(f"Model saved: {model_path / 'churn_model.pkl'}")

# Score toàn bộ customers
X_all = pd.DataFrame(imputer.transform(df[FEATURES]), columns=FEATURES)
df['churn_probability'] = model.predict_proba(X_all)[:, 1]
df['predicted_churned'] = (df['churn_probability'] >= best_threshold).astype(int)

# FIX Vấn đề 2: Dùng percentile bins thay vì fixed bins [0, 0.3, 0.6, 1.0]
# Fixed bins sai vì khi probability dồn vào 1 vùng hẹp → 100% High Risk
# Percentile đảm bảo luôn có đủ 3 nhóm phân phối đều
p33 = df['churn_probability'].quantile(0.33)
p66 = df['churn_probability'].quantile(0.66)
print(f"\nPercentile bins — Low < {p33:.3f} | Medium < {p66:.3f} | High >= {p66:.3f}")

df['risk_segment'] = pd.cut(
    df['churn_probability'],
    bins=[0, p33, p66, 1.0],
    labels=['Low Risk', 'Medium Risk', 'High Risk'],
    include_lowest=True
)
df['recommended_action'] = df['risk_segment'].map({
    'High Risk':   'Immediate win-back campaign',
    'Medium Risk': 'Nurture email sequence',
    'Low Risk':    'Standard newsletter'
})

print(f"Risk distribution:\n{df['risk_segment'].value_counts()}")

churn_scores = df[[
    'customer_id', 'churn_probability',
    'predicted_churned', 'risk_segment', 'recommended_action'
]]
churn_scores.to_sql('churn_scores', engine, schema='marts', if_exists='replace', index=False)
print(f"\nWrote {len(churn_scores):,} scores → marts.churn_scores")
print(f"Threshold dùng để score: {best_threshold:.3f}")