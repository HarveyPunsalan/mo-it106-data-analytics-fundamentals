# MotorPH Terminal Assessment - descriptive, sales, and inferential analysis
# reads the cleaned product and sales data, re-runs the checks, computes the
# numbers used in the report, and runs the four homework tests.
#
# Run from the project root:
#   python3 scripts/MotorPH_Terminal_Assessment_Analysis.py

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "outputs"

PRODUCTS_FILE = DATA_DIR / "MotorPH_Product_List_Cleaned.csv"
SALES_FILE = DATA_DIR / "MotorPH_Sales_Cleaned.csv"
RESULTS_FILE = OUTPUT_DIR / "MotorPH_Inferential_Results.txt"
CHART_FILE = OUTPUT_DIR / "MotorPH_Inferential_Charts.png"

WINDOW_START = pd.Timestamp("2025-06-01")
WINDOW_END = pd.Timestamp("2025-08-31")
ALPHA = 0.05

NAVY = "#16324F"
TEAL = "#2A9D8F"
AMBER = "#E9C46A"
GRAY = "#6B7280"
LIGHT = "#F3F4F6"
BORDER = "#D1D5DB"


def peso(value):
    return f"₱{float(value):,.0f}"


def peso_m(value):
    return f"₱{float(value) / 1_000_000:,.1f}M"


def load_and_check():
    products = pd.read_csv(PRODUCTS_FILE)
    sales = pd.read_csv(SALES_FILE)
    sales["Date"] = pd.to_datetime(sales["Date"], errors="coerce")

    product_names = set(products["Product Name"])
    price_map = dict(zip(products["Product Name"], products["Unit Price"]))

    qa = {
        "products_rows": len(products),
        "sales_rows_loaded": len(sales),
        "missing_products": int(products.isnull().sum().sum()),
        "missing_sales": int(sales.isnull().sum().sum()),
        "duplicate_products": int(products.duplicated().sum()),
        "duplicate_sales": int(sales.duplicated().sum()),
        "unparseable_dates": int(sales["Date"].isna().sum()),
        "unmatched_products": sorted(set(sales["Product"].dropna()) - product_names),
        "price_mismatch": int(
            (sales["Unit Price"] != sales["Product"].map(price_map)).sum()
        ),
        "revenue_mismatch": int(
            (sales["Quantity"] * sales["Unit Price"] != sales["Total"]).sum()
        ),
    }

    outside = sales[~sales["Date"].between(WINDOW_START, WINDOW_END)].copy()
    qa["out_of_period"] = len(outside)
    qa["out_of_period_rows"] = outside

    sales = sales[sales["Date"].between(WINDOW_START, WINDOW_END)].copy()
    sales["Revenue"] = sales["Quantity"] * sales["Unit Price"]
    sales["Month"] = sales["Date"].dt.to_period("M")

    qa["sales_rows_analyzed"] = len(sales)
    qa["units"] = int(sales["Quantity"].sum())
    qa["revenue"] = int(sales["Revenue"].sum())
    qa["transactions"] = len(sales)
    qa["category_revenue"] = int(
        sales.merge(
            products[["Product Name", "Product Category"]],
            left_on="Product",
            right_on="Product Name",
        )["Revenue"].sum()
    )
    qa["monthly_revenue"] = int(sales.groupby("Month")["Revenue"].sum().sum())

    qa["quality_ok"] = (
        qa["missing_products"] == 0
        and qa["missing_sales"] == 0
        and qa["duplicate_products"] == 0
        and qa["duplicate_sales"] == 0
        and qa["unparseable_dates"] == 0
        and not qa["unmatched_products"]
        and qa["price_mismatch"] == 0
        and qa["revenue_mismatch"] == 0
        and qa["out_of_period"] == 1
        and qa["sales_rows_analyzed"] == 990
        and qa["units"] == 17_534
        and qa["revenue"] == 4_441_540_000
        and qa["category_revenue"] == qa["revenue"]
        and qa["monthly_revenue"] == qa["revenue"]
    )

    if not qa["quality_ok"]:
        raise ValueError("Data quality gate failed. Check the QA values.")

    return products, sales, qa


def product_summary(products):
    prices = products["Unit Price"].astype(float)
    top_prices = products.nlargest(5, "Unit Price")
    return {
        "products": len(products),
        "categories": products["Product Category"].nunique(),
        "mean_price": prices.mean(),
        "median_price": prices.median(),
        "min_price": prices.min(),
        "max_price": prices.max(),
        "sd_price": prices.std(ddof=1),
        "q1_price": prices.quantile(0.25),
        "q3_price": prices.quantile(0.75),
        "list_value": prices.sum(),
        "top5_value": top_prices["Unit Price"].sum(),
        "top5_share": top_prices["Unit Price"].sum() / prices.sum(),
        "category_counts": products["Product Category"].value_counts().sort_index(),
        "acquisition_years": products["Acquisition Year"].value_counts().sort_index(),
        "manufacturing_years": products["Manufacturing Year"].value_counts().sort_index(),
        "top_prices": top_prices[["Product Name", "Product Category", "Unit Price"]],
    }


def sales_summary(products, sales):
    monthly = (
        sales.groupby("Month")
        .agg(Revenue=("Revenue", "sum"), Units=("Quantity", "sum"), Transactions=("Revenue", "size"))
        .reset_index()
    )
    monthly["AOV"] = monthly["Revenue"] / monthly["Transactions"]
    monthly["ASP"] = monthly["Revenue"] / monthly["Units"]

    merged = sales.merge(
        products[["Product Name", "Product Category"]],
        left_on="Product",
        right_on="Product Name",
    )
    category = (
        merged.groupby("Product Category")
        .agg(Units=("Quantity", "sum"), Revenue=("Revenue", "sum"))
        .reset_index()
    )
    model_counts = products["Product Category"].value_counts()
    category["Models"] = category["Product Category"].map(model_counts)
    category["ASP"] = category["Revenue"] / category["Units"]
    category["RevenueShare"] = category["Revenue"] / category["Revenue"].sum()
    category["UnitsShare"] = category["Units"] / category["Units"].sum()
    category = category.sort_values("Revenue", ascending=False)

    client = (
        sales.groupby("Client Type")
        .agg(Revenue=("Revenue", "sum"), Units=("Quantity", "sum"), Transactions=("Revenue", "size"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    client["RevenueShare"] = client["Revenue"] / client["Revenue"].sum()

    monthly_client = (
        sales.pivot_table(
            index="Month", columns="Client Type", values="Revenue", aggfunc="sum", fill_value=0
        )
        .reset_index()
    )

    products_sales = (
        sales.groupby("Product")
        .agg(Units=("Quantity", "sum"), Revenue=("Revenue", "sum"))
        .reset_index()
    )
    top_revenue = products_sales.sort_values("Revenue", ascending=False).head(10)
    top_units = products_sales.sort_values("Units", ascending=False).head(10)

    heritage = products_sales.merge(
        products[products["Product Category"] == "Heritage"][["Product Name"]],
        left_on="Product",
        right_on="Product Name",
    ).sort_values("Revenue", ascending=False)

    return {
        "monthly": monthly,
        "category": category,
        "client": client,
        "monthly_client": monthly_client,
        "top_revenue": top_revenue,
        "top_units": top_units,
        "heritage": heritage,
    }


def daily_series(sales):
    dates = pd.date_range(WINDOW_START, WINDOW_END, freq="D")
    daily_revenue = sales.groupby("Date")["Revenue"].sum().reindex(dates, fill_value=0)
    daily_units = sales.groupby("Date")["Quantity"].sum().reindex(dates, fill_value=0)
    daily_retail = (
        sales[sales["Client Type"] == "Retail"]
        .groupby("Date")["Revenue"]
        .sum()
        .reindex(dates, fill_value=0)
    )
    return daily_revenue, daily_units, daily_retail


def normality(values):
    values = np.asarray(values, dtype=float)
    result = stats.shapiro(values)
    return {
        "n": len(values),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "sd": float(np.std(values, ddof=1)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "skew": float(stats.skew(values, bias=False)),
        "kurtosis": float(stats.kurtosis(values, fisher=True, bias=False)),
        "W": float(result.statistic),
        "p": float(result.pvalue),
        "reject": bool(result.pvalue < ALPHA),
    }


def comparison(first, second):
    first = np.asarray(first, dtype=float)
    second = np.asarray(second, dtype=float)
    result = stats.mannwhitneyu(first, second, alternative="greater")
    u = float(result.statistic)
    rbc = 2 * u / (len(first) * len(second)) - 1
    return {
        "n1": len(first),
        "n2": len(second),
        "mean1": float(np.mean(first)),
        "mean2": float(np.mean(second)),
        "median1": float(np.median(first)),
        "median2": float(np.median(second)),
        "sd1": float(np.std(first, ddof=1)),
        "sd2": float(np.std(second, ddof=1)),
        "U": u,
        "p": float(result.pvalue),
        "rbc": float(rbc),
        "reject": bool(result.pvalue < ALPHA),
    }


def run_tests(products, sales):
    all_products = products["Product Name"].tolist()

    july = sales[sales["Date"].dt.month == 7].groupby("Product")["Revenue"].sum()
    august = sales[sales["Date"].dt.month == 8].groupby("Product")["Revenue"].sum()
    july_values = july.reindex(all_products, fill_value=0).astype(float)
    august_values = august.reindex(all_products, fill_value=0).astype(float)

    daily_revenue, daily_units, daily_retail = daily_series(sales)

    june_retail = daily_retail[daily_retail.index.month == 6]
    july_retail = daily_retail[daily_retail.index.month == 7]
    august_units = daily_units[daily_units.index.month == 8]
    previous_units = daily_units[daily_units.index.month.isin([6, 7])]

    return {
        "july_values": july_values,
        "august_values": august_values,
        "july_normality": normality(july_values),
        "august_normality": normality(august_values),
        "retail_june": june_retail,
        "retail_july": july_retail,
        "retail_test": comparison(july_retail, june_retail),
        "units_august": august_units,
        "units_previous": previous_units,
        "units_test": comparison(august_units, previous_units),
        "daily_revenue": daily_revenue,
        "daily_units": daily_units,
        "daily_retail": daily_retail,
    }


def build_chart(results):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.patch.set_facecolor("white")

    # Q1: July product revenue
    ax = axes[0, 0]
    values = results["july_values"] / 1_000_000
    ax.hist(values, bins=12, color=NAVY, edgecolor="white", linewidth=0.8)
    ax.axvline(values.mean(), color=AMBER, linewidth=2, label=f"Mean {peso_m(values.mean() * 1_000_000)}")
    ax.axvline(values.median(), color=TEAL, linewidth=2, linestyle="--", label=f"Median {peso_m(values.median() * 1_000_000)}")
    ax.set_title("Q1. July 2025 product revenue", loc="left", fontsize=12, color=NAVY, fontweight="bold")
    ax.set_xlabel("Revenue per product (₱ millions)")
    ax.set_ylabel("Number of products")
    ax.legend(frameon=False, fontsize=8)
    ax.text(
        0.99,
        0.95,
        f"Shapiro-Wilk p = {results['july_normality']['p']:.3g}\nSkew = {results['july_normality']['skew']:.2f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color=GRAY,
    )

    # Q2: daily retail revenue, June vs July
    ax = axes[0, 1]
    data = [results["retail_june"] / 1_000_000, results["retail_july"] / 1_000_000]
    box = ax.boxplot(
        data,
        tick_labels=["June", "July"],
        patch_artist=True,
        widths=0.45,
        medianprops=dict(color=NAVY, linewidth=2),
        boxprops=dict(linewidth=1),
        whiskerprops=dict(linewidth=1),
        capprops=dict(linewidth=1),
        flierprops=dict(marker="o", markersize=3, markerfacecolor=GRAY, markeredgecolor=GRAY),
    )
    for patch, color in zip(box["boxes"], [TEAL, AMBER]):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    rng = np.random.default_rng(7)
    for i, series in enumerate(data, start=1):
        ax.scatter(
            np.full(len(series), i) + rng.normal(0, 0.035, len(series)),
            series,
            s=10,
            color=NAVY,
            alpha=0.45,
            zorder=3,
        )
    ax.set_title("Q2. Daily retail revenue, June vs July", loc="left", fontsize=12, color=NAVY, fontweight="bold")
    ax.set_ylabel("Revenue per day (₱ millions)")
    ax.text(
        0.99,
        0.95,
        f"One-sided Mann-Whitney p = {results['retail_test']['p']:.3g}\nJuly median {peso_m(results['retail_test']['median1'])}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color=GRAY,
    )

    # Q3: August product revenue
    ax = axes[1, 0]
    values = results["august_values"] / 1_000_000
    ax.hist(values, bins=12, color=NAVY, edgecolor="white", linewidth=0.8)
    ax.axvline(values.mean(), color=AMBER, linewidth=2, label=f"Mean {peso_m(values.mean() * 1_000_000)}")
    ax.axvline(values.median(), color=TEAL, linewidth=2, linestyle="--", label=f"Median {peso_m(values.median() * 1_000_000)}")
    ax.set_title("Q3. August 2025 product revenue", loc="left", fontsize=12, color=NAVY, fontweight="bold")
    ax.set_xlabel("Revenue per product (₱ millions)")
    ax.set_ylabel("Number of products")
    ax.legend(frameon=False, fontsize=8)
    ax.text(
        0.99,
        0.95,
        f"Shapiro-Wilk p = {results['august_normality']['p']:.3g}\nSkew = {results['august_normality']['skew']:.2f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color=GRAY,
    )

    # Q4: daily units, previous months vs August
    ax = axes[1, 1]
    data = [results["units_previous"], results["units_august"]]
    box = ax.boxplot(
        data,
        tick_labels=["June-July", "August"],
        patch_artist=True,
        widths=0.45,
        medianprops=dict(color=NAVY, linewidth=2),
        boxprops=dict(linewidth=1),
        whiskerprops=dict(linewidth=1),
        capprops=dict(linewidth=1),
        flierprops=dict(marker="o", markersize=3, markerfacecolor=GRAY, markeredgecolor=GRAY),
    )
    for patch, color in zip(box["boxes"], [TEAL, AMBER]):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    rng = np.random.default_rng(11)
    for i, series in enumerate(data, start=1):
        ax.scatter(
            np.full(len(series), i) + rng.normal(0, 0.035, len(series)),
            series,
            s=10,
            color=NAVY,
            alpha=0.45,
            zorder=3,
        )
    ax.set_title("Q4. Daily units sold, June-July vs August", loc="left", fontsize=12, color=NAVY, fontweight="bold")
    ax.set_ylabel("Units per day")
    ax.text(
        0.99,
        0.95,
        f"One-sided Mann-Whitney p = {results['units_test']['p']:.3g}\nAugust median {results['units_test']['median1']:.0f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color=GRAY,
    )

    for ax in axes.flat:
        ax.set_facecolor(LIGHT)
        ax.grid(axis="y", color=BORDER, linewidth=0.6, alpha=0.8)
        ax.set_axisbelow(True)
        for side in ["top", "right"]:
            ax.spines[side].set_visible(False)
        for side in ["left", "bottom"]:
            ax.spines[side].set_color(BORDER)

    fig.tight_layout(pad=2.0)
    fig.savefig(CHART_FILE, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_results(qa, product, sales, results):
    lines = []
    add = lines.append

    add("MOTORPH TERMINAL ASSESSMENT - ANALYSIS RESULTS")
    add("=" * 55)
    add("")
    add("DATA AND QA")
    add(f"  Product rows: {qa['products_rows']}")
    add(f"  Sales rows loaded: {qa['sales_rows_loaded']}")
    add(f"  Sales rows analyzed: {qa['sales_rows_analyzed']}")
    add(f"  Date window: {WINDOW_START.date()} to {WINDOW_END.date()}")
    add(f"  Out-of-period rows excluded: {qa['out_of_period']}")
    for _, row in qa["out_of_period_rows"].iterrows():
        add(
            f"    {row['Date'].date()} | {row['Product']} | "
            f"{int(row['Quantity'])} units | {peso(row['Total'])}"
        )
    add(f"  Units: {qa['units']:,}")
    add(f"  Revenue: {peso(qa['revenue'])}")
    add(f"  Transactions: {qa['transactions']:,}")
    add(f"  Missing values (products / sales): {qa['missing_products']} / {qa['missing_sales']}")
    add(f"  Duplicate rows (products / sales): {qa['duplicate_products']} / {qa['duplicate_sales']}")
    add(f"  Unparseable dates: {qa['unparseable_dates']}")
    add(f"  Unmatched product names: {qa['unmatched_products']}")
    add(f"  Price mismatch vs product list: {qa['price_mismatch']}")
    add(f"  Quantity x Unit Price != Total: {qa['revenue_mismatch']}")
    add(f"  Category revenue sum: {peso(qa['category_revenue'])}")
    add(f"  Monthly revenue sum: {peso(qa['monthly_revenue'])}")
    add(f"  Status: {'PASS' if qa['quality_ok'] else 'FAIL'}")
    add("")

    add("PRODUCT SUMMARY (MS1)")
    add(f"  Products: {product['products']}")
    add(f"  Categories: {product['categories']}")
    add(f"  Mean price: {peso(product['mean_price'])}")
    add(f"  Median price: {peso(product['median_price'])}")
    add(f"  Minimum price: {peso(product['min_price'])}")
    add(f"  Maximum price: {peso(product['max_price'])}")
    add(f"  Standard deviation: {peso(product['sd_price'])}")
    add(f"  Q1 price: {peso(product['q1_price'])}")
    add(f"  Q3 price: {peso(product['q3_price'])}")
    add(f"  Total inventory cost (one unit each): {peso(product['list_value'])}")
    add(f"  Top 5 price share: {product['top5_share'] * 100:.1f}%")
    add("")
    add("  Category counts:")
    for name, count in product["category_counts"].items():
        add(f"    {name}: {count}")
    add("")
    add("  Acquisition years:")
    for year, count in product["acquisition_years"].items():
        add(f"    {year}: {count}")
    add("")
    add("  Top 5 prices:")
    for _, row in product["top_prices"].iterrows():
        add(f"    {row['Product Name']} | {row['Product Category']} | {peso(row['Unit Price'])}")
    add("")

    add("SALES SUMMARY (MS2)")
    add("  Monthly:")
    for _, row in sales["monthly"].iterrows():
        add(
            f"    {row['Month']} | revenue {peso(row['Revenue'])} | units {int(row['Units']):,} | "
            f"transactions {int(row['Transactions'])} | AOV {peso(row['AOV'])} | ASP {peso(row['ASP'])}"
        )
    add("")
    add("  Category:")
    for _, row in sales["category"].iterrows():
        add(
            f"    {row['Product Category']} | models {int(row['Models'])} | units {int(row['Units']):,} | "
            f"revenue {peso(row['Revenue'])} | ASP {peso(row['ASP'])} | "
            f"revenue share {row['RevenueShare'] * 100:.1f}% | units share {row['UnitsShare'] * 100:.1f}%"
        )
    add("")
    add("  Client type:")
    for _, row in sales["client"].iterrows():
        add(
            f"    {row['Client Type']} | revenue {peso(row['Revenue'])} | units {int(row['Units']):,} | "
            f"transactions {int(row['Transactions'])} | revenue share {row['RevenueShare'] * 100:.1f}%"
        )
    add("")
    add("  Monthly by client:")
    for _, row in sales["monthly_client"].iterrows():
        parts = [f"{col} {peso(row[col])}" for col in sales["monthly_client"].columns if col != "Month"]
        add(f"    {row['Month']} | " + " | ".join(parts))
    add("")
    add("  Top 10 products by revenue:")
    for _, row in sales["top_revenue"].iterrows():
        add(f"    {row['Product']} | {int(row['Units']):,} units | {peso(row['Revenue'])}")
    add("")
    add("  Top 10 products by units:")
    for _, row in sales["top_units"].iterrows():
        add(f"    {row['Product']} | {int(row['Units']):,} units | {peso(row['Revenue'])}")
    add("")
    add("  Heritage trace:")
    for _, row in sales["heritage"].iterrows():
        add(f"    {row['Product']} | {int(row['Units']):,} units | {peso(row['Revenue'])}")
    add("")

    add("INFERENTIAL ANALYSIS")
    add(f"  Alpha: {ALPHA}")
    add("")

    july = results["july_normality"]
    add("  Q1. Is the distribution of July 2025 product sales normal?")
    add("    H0: The July 2025 product revenue distribution is normal.")
    add("    H1: The July 2025 product revenue distribution is not normal.")
    add("    Unit: July revenue for each of the 50 products. KTM Duke 200 had no July sales, so its value is 0.")
    add(f"    n: {july['n']}")
    add(f"    Mean: {peso(july['mean'])}")
    add(f"    Median: {peso(july['median'])}")
    add(f"    Standard deviation: {peso(july['sd'])}")
    add(f"    Minimum: {peso(july['min'])}")
    add(f"    Maximum: {peso(july['max'])}")
    add(f"    Skewness: {july['skew']:.3f}")
    add(f"    Kurtosis: {july['kurtosis']:.3f}")
    add(f"    Shapiro-Wilk W: {july['W']:.4f}")
    add(f"    p-value: {july['p']:.6g}")
    add(f"    Decision: {'Reject H0' if july['reject'] else 'Fail to reject H0'}")
    add("    Interpretation: The distribution is right-skewed. A few premium models earn")
    add("    much more than the median product, so the July product sales are not normal.")
    add("")

    q2 = results["retail_test"]
    add("  Q2. Are July 2025 retail sales greater than June 2025 retail sales?")
    add("    H0: July daily retail revenue is less than or equal to June daily retail revenue.")
    add("    H1: July daily retail revenue is greater than June daily retail revenue.")
    add("    Unit: Daily retail revenue. June has 30 days, July has 31 days.")
    add(f"    June: n {q2['n2']}, mean {peso(q2['mean2'])}, median {peso(q2['median2'])}, sd {peso(q2['sd2'])}")
    add(f"    July: n {q2['n1']}, mean {peso(q2['mean1'])}, median {peso(q2['median1'])}, sd {peso(q2['sd1'])}")
    add(f"    Mann-Whitney U: {q2['U']:.1f}")
    add(f"    p-value: {q2['p']:.6g}")
    add(f"    Rank-biserial: {q2['rbc']:.3f}")
    add(f"    Decision: {'Reject H0' if q2['reject'] else 'Fail to reject H0'}")
    add("    Interpretation: The July daily retail revenue is lower, not higher. The data do")
    add("    not support the claim that July retail sales were greater than June.")
    add("")

    august = results["august_normality"]
    add("  Q3. Is the distribution of August 2025 product sales normal?")
    add("    H0: The August 2025 product revenue distribution is normal.")
    add("    H1: The August 2025 product revenue distribution is not normal.")
    add("    Unit: August revenue for each of the 50 products.")
    add(f"    n: {august['n']}")
    add(f"    Mean: {peso(august['mean'])}")
    add(f"    Median: {peso(august['median'])}")
    add(f"    Standard deviation: {peso(august['sd'])}")
    add(f"    Minimum: {peso(august['min'])}")
    add(f"    Maximum: {peso(august['max'])}")
    add(f"    Skewness: {august['skew']:.3f}")
    add(f"    Kurtosis: {august['kurtosis']:.3f}")
    add(f"    Shapiro-Wilk W: {august['W']:.4f}")
    add(f"    p-value: {august['p']:.6g}")
    add(f"    Decision: {'Reject H0' if august['reject'] else 'Fail to reject H0'}")
    add("    Interpretation: The August distribution is also right-skewed. A few premium")
    add("    models pull the mean above the median, so the distribution is not normal.")
    add("")

    q4 = results["units_test"]
    add("  Q4. Were more products sold in August 2025 than in the previous months?")
    add("    H0: August daily units are less than or equal to the June-July daily units.")
    add("    H1: August daily units are greater than the June-July daily units.")
    add("    Unit: Daily units sold. August has 31 days, June-July has 61 days.")
    add(f"    Previous (June-July): n {q4['n2']}, mean {q4['mean2']:.1f}, median {q4['median2']:.1f}, sd {q4['sd2']:.1f}")
    add(f"    August: n {q4['n1']}, mean {q4['mean1']:.1f}, median {q4['median1']:.1f}, sd {q4['sd1']:.1f}")
    add(f"    Mann-Whitney U: {q4['U']:.1f}")
    add(f"    p-value: {q4['p']:.6g}")
    add(f"    Rank-biserial: {q4['rbc']:.3f}")
    add(f"    Decision: {'Reject H0' if q4['reject'] else 'Fail to reject H0'}")
    add("    Interpretation: August daily units are lower, not higher. The data do not")
    add("    support the claim that more products were sold in August.")
    add("")

    add("SUMMARY")
    add("  Question | Test | Statistic | p-value | Decision")
    add(
        f"  Q1 July normality | Shapiro-Wilk | W = {july['W']:.4f} | {july['p']:.6g} | "
        f"{'Reject H0' if july['reject'] else 'Fail to reject H0'}"
    )
    add(
        f"  Q2 July retail > June | Mann-Whitney U | U = {q2['U']:.1f} | {q2['p']:.6g} | "
        f"{'Reject H0' if q2['reject'] else 'Fail to reject H0'}"
    )
    add(
        f"  Q3 August normality | Shapiro-Wilk | W = {august['W']:.4f} | {august['p']:.6g} | "
        f"{'Reject H0' if august['reject'] else 'Fail to reject H0'}"
    )
    add(
        f"  Q4 August units > previous | Mann-Whitney U | U = {q4['U']:.1f} | {q4['p']:.6g} | "
        f"{'Reject H0' if q4['reject'] else 'Fail to reject H0'}"
    )
    add("")

    RESULTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def main():
    products, sales, qa = load_and_check()
    product = product_summary(products)
    sales_data = sales_summary(products, sales)
    results = run_tests(products, sales)

    build_chart(results)
    lines = write_results(qa, product, sales_data, results)

    print("\n".join(lines[:35]))
    print("...")
    print("\n".join(lines[-18:]))
    print(f"\nSaved: {RESULTS_FILE.name}, {CHART_FILE.name}")


if __name__ == "__main__":
    main()
