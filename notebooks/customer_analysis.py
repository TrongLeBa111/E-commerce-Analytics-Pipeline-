import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
import os
import warnings

# --- SETUP ---
warnings.filterwarnings('ignore')
sns.set_theme(style="whitegrid")
plt.rcParams.update({'figure.figsize': (12, 6), 'font.size': 11})

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# --- 1. KẾT NỐI DATABASE ---
load_dotenv(BASE_DIR.parent / ".env")
engine = create_engine(
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@localhost:5432/{os.getenv('POSTGRES_DB')}"
)

def load_data():
    df = pd.read_sql("""
        SELECT f.order_id, f.customer_id, f.order_status, f.purchased_at,
               f.delivered_to_customer_at, f.estimated_delivery_at,
               f.total_order_value, f.delivery_days, c.state
        FROM marts.fct_orders f
        JOIN marts.dim_customers c ON f.customer_id = c.customer_id
    """, engine, parse_dates=['purchased_at', 'delivered_to_customer_at', 'estimated_delivery_at'])
    print(f"✅ Loaded {len(df):,} orders ({df['purchased_at'].min().date()} → {df['purchased_at'].max().date()})")
    return df

df_orders = load_data()


# --- 2. RFM SEGMENTATION ---
print("\n📊 Phân cụm khách hàng RFM...")
ref_date = df_orders['purchased_at'].max() + pd.Timedelta(days=1)

rfm = df_orders.groupby('customer_id').agg(
    recency   = ('purchased_at', lambda x: (ref_date - x.max()).days),
    frequency = ('order_id', 'count'),
    monetary  = ('total_order_value', 'sum')
).reset_index()

rfm['r_score'] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
rfm['m_score'] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

def get_segment(row):
    r, f = int(row['r_score']), int(row['f_score'])
    if r >= 4 and f >= 4: return 'Champions'
    if f >= 3:             return 'Loyal'
    if r >= 4:             return 'New'
    if r <= 2 and f >= 3:  return 'At Risk'
    if r <= 2:             return 'Lost'
    return 'Potential'

rfm['segment'] = rfm.apply(get_segment, axis=1)

# FIX 1: dùng .reset_index() đúng cách sau groupby
total_revenue = rfm['monetary'].sum()
summary = rfm.groupby('segment').agg(
    count       = ('customer_id', 'count'),
    total_rev   = ('monetary', 'sum')
).reset_index()
summary['rev_pct'] = (summary['total_rev'] / total_revenue * 100).round(1)
summary['cus_pct'] = (summary['count'] / summary['count'].sum() * 100).round(1)
summary = summary.sort_values('count', ascending=False)
print(summary[['segment', 'count', 'cus_pct', 'rev_pct']].to_string(index=False))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle('RFM Customer Segmentation', fontsize=15, fontweight='bold')
sns.barplot(data=summary, x='segment', y='count',   ax=ax1, palette='viridis')
sns.barplot(data=summary, x='segment', y='rev_pct', ax=ax2, palette='magma')
ax1.set_title('Số lượng khách hàng')
ax2.set_title('% Đóng góp doanh thu')
ax1.tick_params(axis='x', rotation=30)
ax2.tick_params(axis='x', rotation=30)
for ax, col in zip([ax1, ax2], ['cus_pct', 'rev_pct']):
    for i, row in summary.reset_index().iterrows():
        ax.text(i, row[col] / 2, f"{row[col]}%", ha='center', color='white', fontweight='bold', fontsize=9)
plt.tight_layout()
plt.savefig(RESULTS_DIR / '01_rfm_segments.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Saved: 01_rfm_segments.png")


# --- 3. DELIVERY BY STATE ---
print("\n🗺️ Phân tích giao hàng theo bang...")
df_delivered = df_orders[df_orders['delivery_days'].notna()].copy()
df_delivered['is_late'] = df_delivered['delivered_to_customer_at'] > df_delivered['estimated_delivery_at']

print(f"Late delivery rate: {df_delivered['is_late'].mean()*100:.1f}%")
print(f"Average delivery days: {df_delivered['delivery_days'].mean():.1f}")

state_stats = df_delivered.groupby('state').agg(
    avg_days    = ('delivery_days', 'mean'),
    late_pct    = ('is_late', lambda x: x.mean() * 100),
    order_count = ('order_id', 'count')
).reset_index()
state_stats = state_stats[state_stats['order_count'] >= 100]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle('Delivery Performance by State', fontsize=15, fontweight='bold')

top_slow = state_stats.nlargest(10, 'avg_days')
top_late = state_stats.nlargest(10, 'late_pct')

ax1.barh(top_slow['state'], top_slow['avg_days'], color='steelblue')
ax1.set_title('Top 10 Chậm nhất (ngày TB)')
for i, v in enumerate(top_slow['avg_days']):
    ax1.text(v + 0.2, i, f'{v:.1f}', va='center')

ax2.barh(top_late['state'], top_late['late_pct'], color='coral')
ax2.set_title('Top 10 Tỷ lệ giao trễ (%)')
for i, v in enumerate(top_late['late_pct']):
    ax2.text(v + 0.2, i, f'{v:.1f}%', va='center')

plt.tight_layout()
plt.savefig(RESULTS_DIR / '02_delivery_by_state.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Saved: 02_delivery_by_state.png")


# --- 4. REVIEW SCORE VS DELIVERY ---
print("\n⭐ Review Score vs Delivery Time...")
df_rev = pd.read_sql("""
    SELECT f.order_id, f.delivery_days, r.review_score::int
    FROM marts.fct_orders f
    JOIN raw.order_reviews r ON f.order_id = r.order_id
    WHERE f.delivery_days IS NOT NULL AND r.review_score IS NOT NULL
""", engine)

df_rev['delivery_bucket'] = pd.cut(
    df_rev['delivery_days'],
    bins=[0, 7, 14, 21, 999],
    labels=['≤7 days', '8-14 days', '15-21 days', '>21 days']
)
rev_stats = df_rev.groupby('delivery_bucket', observed=True).agg(
    avg_score = ('review_score', 'mean'),
    count     = ('order_id', 'count')
).reset_index()

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(rev_stats['delivery_bucket'], rev_stats['avg_score'],
              color=['#2ecc71', '#f39c12', '#e67e22', '#e74c3c'])
ax.axhline(df_rev['review_score'].mean(), color='gray', linestyle='--',
           label=f"Overall avg: {df_rev['review_score'].mean():.2f}")
ax.set_ylim(0, 5.5)
ax.set_title('Average Review Score by Delivery Time', fontsize=14, fontweight='bold')
ax.legend()
for bar, (_, row) in zip(bars, rev_stats.iterrows()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
            f"{row['avg_score']:.2f}\n(n={row['count']:,})", ha='center', fontsize=10)
plt.tight_layout()
plt.savefig(RESULTS_DIR / '03_review_vs_delivery.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Saved: 03_review_vs_delivery.png")


# --- 5. MONTHLY TREND ---
print("\n📈 Xu hướng doanh thu theo tháng...")
df_orders['month'] = df_orders['purchased_at'].dt.to_period('M').astype(str)
monthly = df_orders.groupby('month').agg(
    revenue = ('total_order_value', 'sum'),
    orders  = ('order_id', 'count')
).reset_index()

fig, ax1 = plt.subplots(figsize=(14, 6))
ax2 = ax1.twinx()
ax1.bar(monthly['month'], monthly['revenue'], color='steelblue', alpha=0.7, label='Revenue')
ax2.plot(monthly['month'], monthly['orders'], color='coral', marker='o', linewidth=2, label='Orders')
ax1.set_title('Monthly Revenue & Order Count', fontsize=14, fontweight='bold')
ax1.set_ylabel('Revenue (BRL)', color='steelblue')
ax2.set_ylabel('Order Count', color='coral')
ax1.tick_params(axis='x', rotation=45)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
lines = ax1.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
labels = ax1.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
ax1.legend(lines, labels, loc='upper left')
plt.tight_layout()
plt.savefig(RESULTS_DIR / '04_monthly_revenue.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Saved: 04_monthly_revenue.png")


# --- 6. TOP PRODUCT CATEGORIES ---
print("\n🏆 Top Product Categories...")
df_prod = pd.read_sql("""
    SELECT p.category_name_en,
           SUM(oi.price + oi.freight_value) AS revenue,
           COUNT(DISTINCT oi.order_id)       AS orders
    FROM staging.stg_order_items oi
    JOIN marts.dim_products p ON oi.product_id = p.product_id
    WHERE p.category_name_en != 'uncategorized'
    GROUP BY 1 ORDER BY 2 DESC LIMIT 10
""", engine)
print(df_prod.to_string(index=False))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle('Top 10 Product Categories', fontsize=15, fontweight='bold')
sns.barplot(data=df_prod, y='category_name_en', x='revenue', ax=ax1, color='steelblue')
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
ax1.set_title('By Revenue (BRL)')
ax1.set_ylabel('')
sns.barplot(data=df_prod, y='category_name_en', x='orders', ax=ax2, color='coral')
ax2.set_title('By Order Count')
ax2.set_ylabel('')
plt.tight_layout()
plt.savefig(RESULTS_DIR / '05_top_categories.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Saved: 05_top_categories.png")


# --- 7. COHORT RETENTION ---
# Thay cohort bằng: Repeat Purchase Rate by State
print("\n🔄 Repeat Purchase Analysis...")

purchase_freq = df_orders.groupby('customer_id').agg(
    order_count = ('order_id', 'count'),
    state       = ('state', 'first')
).reset_index()

one_time = (purchase_freq['order_count'] == 1).mean() * 100
repeat   = (purchase_freq['order_count'] > 1).mean() * 100
print(f"One-time buyers: {one_time:.1f}%")
print(f"Repeat buyers:   {repeat:.1f}%")

# Pie chart
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Customer Purchase Behavior', fontsize=15, fontweight='bold')

# Chart 1: Pie
ax1.pie([one_time, repeat],
        labels=['One-time\nBuyers', 'Repeat\nBuyers'],
        autopct='%1.1f%%',
        colors=['#e74c3c', '#2ecc71'],
        startangle=90)
ax1.set_title('One-time vs Repeat Buyers')

# Chart 2: Distribution of purchase frequency
freq_dist = purchase_freq['order_count'].value_counts().sort_index().head(6)
ax2.bar(freq_dist.index.astype(str), freq_dist.values, color='steelblue')
ax2.set_title('Purchase Frequency Distribution')
ax2.set_xlabel('Number of Orders')
ax2.set_ylabel('Number of Customers')
for i, v in enumerate(freq_dist.values):
    ax2.text(i, v + 100, f'{v:,}', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig(RESULTS_DIR / '06_repeat_purchase.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Saved: 06_repeat_purchase.png")