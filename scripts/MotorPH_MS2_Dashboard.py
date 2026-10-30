# MotorPH Milestone 2 - analytical dashboard
# reads the cleaned product and sales data, checks it, computes the metrics,
# and builds the four dashboard sections plus a readable inventory table.
#
# Run from the project root:
#   python3 scripts/MotorPH_MS2_Dashboard.py

from pathlib import Path
import textwrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "outputs"

PRODUCTS_FILE = DATA_DIR / "MotorPH_Product_List_Cleaned.csv"
SALES_FILE = DATA_DIR / "MotorPH_Sales_Cleaned.csv"
DASHBOARD_PNG = OUTPUT_DIR / "MotorPH_MS2_Dashboard.png"
INVENTORY_PNG = OUTPUT_DIR / "MotorPH_MS2_Inventory.png"
QA_FILE = OUTPUT_DIR / "MotorPH_MS2_QA.txt"

WINDOW_START = pd.Timestamp("2025-06-01")
WINDOW_END = pd.Timestamp("2025-08-31")

NAVY = "#16324F"
TEAL = "#2A9D8F"
AMBER = "#E9C46A"
GRAY = "#6B7280"
LIGHT = "#F3F4F6"
BORDER = "#D1D5DB"


def peso_short(value):
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"₱{value / 1_000_000_000:,.2f}B"
    if abs(value) >= 1_000_000:
        return f"₱{value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"₱{value / 1_000:,.0f}K"
    return f"₱{value:,.0f}"


def peso_full(value):
    return f"₱{float(value):,.0f}"


def load_data():
    products = pd.read_csv(PRODUCTS_FILE)
    sales = pd.read_csv(SALES_FILE)
    sales["Date"] = pd.to_datetime(sales["Date"], errors="coerce")
    return products, sales


def validate_and_filter(products, sales):
    """Run the quality checks before any chart or metric is computed."""
    qa = {
        "products_rows": len(products),
        "sales_rows_loaded": len(sales),
        "missing_products": int(products.isnull().sum().sum()),
        "missing_sales": int(sales.isnull().sum().sum()),
        "duplicate_products": int(products.duplicated().sum()),
        "duplicate_sales": int(sales.duplicated().sum()),
        "unparseable_dates": int(sales["Date"].isna().sum()),
    }

    product_names = set(products["Product Name"])
    qa["unmatched_products"] = sorted(set(sales["Product"].dropna()) - product_names)

    price_map = dict(zip(products["Product Name"], products["Unit Price"]))
    qa["price_mismatch"] = int(
        (sales["Unit Price"] != sales["Product"].map(price_map)).sum()
    )
    qa["revenue_mismatch"] = int(
        (sales["Quantity"] * sales["Unit Price"] != sales["Total"]).sum()
    )

    outside = sales[~sales["Date"].between(WINDOW_START, WINDOW_END)].copy()
    qa["out_of_period"] = len(outside)
    qa["out_of_period_rows"] = outside

    sales = sales[sales["Date"].between(WINDOW_START, WINDOW_END)].copy()
    sales["Revenue"] = sales["Quantity"] * sales["Unit Price"]

    qa["sales_rows_analyzed"] = len(sales)
    qa["date_min"] = sales["Date"].min()
    qa["date_max"] = sales["Date"].max()
    qa["quality_ok"] = (
        qa["missing_products"] == 0
        and qa["missing_sales"] == 0
        and qa["duplicate_products"] == 0
        and qa["duplicate_sales"] == 0
        and qa["unparseable_dates"] == 0
        and not qa["unmatched_products"]
        and qa["price_mismatch"] == 0
        and qa["revenue_mismatch"] == 0
        and qa["sales_rows_analyzed"] > 0
        and bool((sales["Quantity"] * sales["Unit Price"] == sales["Total"]).all())
    )

    if not qa["quality_ok"]:
        raise ValueError(
            "Data quality gate failed. Check the QA dictionary for the failing check."
        )

    return products, sales, qa


def compute_metrics(products, sales):
    merged = sales.merge(
        products[["Product Name", "Product Category"]],
        left_on="Product",
        right_on="Product Name",
        how="left",
    )

    category = merged.groupby("Product Category").agg(
        models=("Product Name", "nunique"),
        units=("Quantity", "sum"),
        revenue=("Revenue", "sum"),
        transactions=("Revenue", "count"),
    )
    category["revenue_share"] = category["revenue"] / category["revenue"].sum() * 100
    category["units_share"] = category["units"] / category["units"].sum() * 100
    category["revenue_per_model"] = category["revenue"] / category["models"]
    category["units_per_model"] = category["units"] / category["models"]
    category["avg_selling_price"] = category["revenue"] / category["units"]
    category = category.sort_values("revenue", ascending=False)

    monthly = (
        merged.assign(Month=merged["Date"].dt.to_period("M"))
        .groupby("Month")
        .agg(
            revenue=("Revenue", "sum"),
            units=("Quantity", "sum"),
            transactions=("Revenue", "count"),
        )
        .sort_index()
    )

    client = (
        merged.groupby("Client Type")
        .agg(revenue=("Revenue", "sum"), units=("Quantity", "sum"))
        .sort_values("revenue", ascending=False)
    )
    client["revenue_share"] = client["revenue"] / client["revenue"].sum() * 100

    products_performance = merged.groupby("Product").agg(
        units=("Quantity", "sum"),
        revenue=("Revenue", "sum"),
    )
    top_products = products_performance.sort_values("revenue", ascending=False)

    inventory = products.merge(
        products_performance,
        left_on="Product Name",
        right_index=True,
        how="left",
    )
    inventory[["units", "revenue"]] = inventory[["units", "revenue"]].fillna(0)
    inventory = inventory.rename(
        columns={
            "Product ID Number": "id",
            "Product Name": "product",
            "Product Category": "category",
            "Unit Price": "price",
        }
    )
    inventory = inventory.sort_values("id")

    heritage = merged[merged["Product Category"] == "Heritage"]
    heritage_trace = (
        heritage.groupby("Product")
        .agg(units=("Quantity", "sum"), revenue=("Revenue", "sum"))
        .sort_values("revenue", ascending=False)
    )

    overview = {
        "total_products": len(products),
        "total_categories": int(products["Product Category"].nunique()),
        "total_units": int(merged["Quantity"].sum()),
        "total_revenue": float(merged["Revenue"].sum()),
        "transactions": int(len(merged)),
        "avg_order_value": float(merged["Revenue"].sum() / len(merged)),
        "top_category_revenue": category["revenue"].idxmax(),
        "top_category_units": category["units"].idxmax(),
        "top_product_revenue": top_products["revenue"].idxmax(),
        "date_min": merged["Date"].min(),
        "date_max": merged["Date"].max(),
    }

    return {
        "merged": merged,
        "category": category,
        "monthly": monthly,
        "client": client,
        "top_products": top_products,
        "inventory": inventory,
        "heritage_trace": heritage_trace,
        "overview": overview,
    }


def section_header(fig, cell, number, title):
    ax = fig.add_subplot(cell)
    ax.set_facecolor(NAVY)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.text(
        0.006,
        0.5,
        f"{number:02d}",
        transform=ax.transAxes,
        color=AMBER,
        fontsize=13,
        fontweight="bold",
        va="center",
    )
    ax.text(
        0.042,
        0.5,
        title,
        transform=ax.transAxes,
        color="white",
        fontsize=12.5,
        fontweight="bold",
        va="center",
    )
    return ax


def kpi_tile(ax, label, value, sublabel):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(
        FancyBboxPatch(
            (0.02, 0.06),
            0.96,
            0.88,
            boxstyle="round,pad=0.02,rounding_size=0.04",
            facecolor=LIGHT,
            edgecolor=BORDER,
            linewidth=0.8,
        )
    )
    ax.text(0.5, 0.78, label, ha="center", va="center", fontsize=9, color=GRAY)
    value_size = 11.5 if "\n" in value else 15.5
    ax.text(
        0.5,
        0.47,
        value,
        ha="center",
        va="center",
        fontsize=value_size,
        fontweight="bold",
        color=NAVY,
        linespacing=1.05,
    )
    ax.text(0.5, 0.16, sublabel, ha="center", va="center", fontsize=8, color=GRAY)


def clean_axis(ax):
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors="#111827")
    ax.grid(axis="x", color=BORDER, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def build_category_panel(ax, category, order, column, title, xlabel, color, formatter):
    values = category.loc[order, column]
    ax.barh(order, values, color=color, height=0.68)
    peak = float(values.max())
    for i, value in enumerate(values):
        ax.text(
            value + peak * 0.015,
            i,
            formatter(value),
            va="center",
            fontsize=7.4,
            color="#111827",
        )
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=7.6)
    ax.set_xlim(0, peak * 1.22)
    ax.set_xlabel(xlabel, fontsize=8.5)
    ax.set_title(title, fontsize=11, fontweight="bold", color=NAVY, loc="left")
    clean_axis(ax)


def style_table(table, header_fill=NAVY):
    table.auto_set_font_size(False)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("white")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_facecolor(header_fill)
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("white" if row % 2 else LIGHT)
            cell.set_text_props(color="#111827")
            if col in (0, 3, 4, 5):
                cell.set_text_props(ha="right")


def inventory_table(ax, chunk, fontsize):
    ax.axis("off")
    headers = ["ID", "Product", "Category", "Unit Price", "Units", "Revenue"]
    rows = []
    for _, row in chunk.iterrows():
        rows.append(
            [
                f"{int(row['id'])}",
                str(row["product"]),
                str(row["category"]),
                peso_full(row["price"]),
                f"{int(row['units']):,}",
                peso_full(row["revenue"]),
            ]
        )
    table = ax.table(
        cellText=rows,
        colLabels=headers,
        loc="center",
        cellLoc="left",
        colLoc="center",
        colWidths=[0.055, 0.34, 0.17, 0.145, 0.09, 0.20],
        bbox=[0, 0, 1, 1],
    )
    table.set_fontsize(fontsize)
    style_table(table)
    return table


def build_dashboard(metrics, qa):
    overview = metrics["overview"]
    category = metrics["category"]
    monthly = metrics["monthly"]
    client = metrics["client"]
    top_products = metrics["top_products"]
    inventory = metrics["inventory"]

    fig = plt.figure(figsize=(16, 22.5), facecolor="white")
    gs = GridSpec(
        10,
        3,
        figure=fig,
        height_ratios=[0.32, 1.25, 0.32, 2.5, 2.5, 0.32, 4.6, 0.32, 6.7, 0.35],
        hspace=0.50,
        wspace=0.30,
        left=0.045,
        right=0.97,
        top=0.935,
        bottom=0.025,
    )

    fig.text(
        0.5,
        0.977,
        "MotorPH Analytical Dashboard",
        fontsize=22,
        fontweight="bold",
        color=NAVY,
        ha="center",
    )
    fig.text(
        0.5,
        0.954,
        "Product lineup and Q3 2025 sales performance  |  June 1 – August 31, 2025",
        fontsize=10.5,
        color=GRAY,
        ha="center",
    )

    section_header(fig, gs[0, :], 1, "MOTORPH OVERVIEW")

    top_cat = overview["top_category_revenue"]
    top_cat_row = category.loc[top_cat]
    top_product = overview["top_product_revenue"]
    top_product_row = top_products.loc[top_product]
    tiles = [
        ("Products", f"{overview['total_products']}", f"{overview['total_categories']} categories"),
        ("Units sold", f"{overview['total_units']:,}", "June – August 2025"),
        ("Revenue", peso_short(overview["total_revenue"]), "Quantity × Unit Price"),
        ("Transactions", f"{overview['transactions']:,}", f"Avg order {peso_short(overview['avg_order_value'])}"),
        ("Top category", top_cat, f"{peso_short(top_cat_row['revenue'])} · {top_cat_row['revenue_share']:.1f}%"),
        (
            "Top product",
            textwrap.fill(top_product, 12),
            f"{peso_short(top_product_row['revenue'])} · {int(top_product_row['units']):,} units",
        ),
    ]
    kpi_gs = gs[1, :].subgridspec(1, 6, wspace=0.18)
    for i, (label, value, sublabel) in enumerate(tiles):
        kpi_tile(fig.add_subplot(kpi_gs[0, i]), label, value, sublabel)

    section_header(fig, gs[2, :], 2, "SALES PERFORMANCE")

    ax_trend = fig.add_subplot(gs[3, :])
    x = list(range(len(monthly)))
    y = monthly["revenue"].to_numpy() / 1_000_000
    labels = [period.strftime("%b") for period in monthly.index]
    ax_trend.bar(x, y, color=TEAL, width=0.55, zorder=3)
    for i, value in enumerate(y):
        ax_trend.annotate(
            f"₱{value:,.1f}M",
            (i, value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=9,
            color=NAVY,
            fontweight="bold",
        )
    change = (y[-1] - y[0]) / y[0] * 100
    ax_trend.text(
        0.99,
        0.90,
        f"{change:+.1f}% June → August",
        transform=ax_trend.transAxes,
        ha="right",
        va="top",
        fontsize=9.5,
        color=GRAY,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=BORDER),
    )
    ax_trend.set_xticks(x)
    ax_trend.set_xticklabels(labels, fontsize=10)
    ax_trend.set_ylim(0, float(y.max()) * 1.16)
    ax_trend.set_ylabel("Revenue (₱ million)", fontsize=9.5)
    ax_trend.set_title("Monthly revenue trend", fontsize=11.5, fontweight="bold", color=NAVY, loc="left")
    ax_trend.grid(axis="y", color=BORDER, linewidth=0.6, alpha=0.7)
    ax_trend.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax_trend.spines[spine].set_visible(False)

    ax_top = fig.add_subplot(gs[4, :2])
    top5 = top_products.head(5).sort_values("revenue")
    top5_values = top5["revenue"] / 1_000_000
    ax_top.barh(top5.index, top5_values, color=NAVY, height=0.58)
    peak = float(top5_values.max())
    for i, value in enumerate(top5_values):
        ax_top.text(
            value + peak * 0.015,
            i,
            f"₱{value:,.1f}M",
            va="center",
            fontsize=8.2,
            color="#111827",
        )
    ax_top.set_xlim(0, peak * 1.20)
    ax_top.set_title("Top 5 products by revenue (₱M)", fontsize=11, fontweight="bold", color=NAVY, loc="left")
    ax_top.tick_params(axis="y", labelsize=8.2)
    clean_axis(ax_top)

    ax_client = fig.add_subplot(gs[4, 2])
    client_plot = client.sort_values("revenue")
    client_values = client_plot["revenue"] / 1_000_000
    ax_client.barh(client_plot.index, client_values, color=AMBER, height=0.55)
    client_peak = float(client_values.max())
    for i, (_, row) in enumerate(client_plot.iterrows()):
        ax_client.text(
            row["revenue"] / 1_000_000 + client_peak * 0.015,
            i,
            f"₱{row['revenue'] / 1_000_000:,.0f}M · {row['revenue_share']:.1f}%",
            va="center",
            fontsize=7.8,
            color="#111827",
        )
    ax_client.set_xlim(0, client_peak * 1.35)
    ax_client.set_title("Revenue by client type (₱M)", fontsize=11, fontweight="bold", color=NAVY, loc="left")
    ax_client.tick_params(axis="y", labelsize=8.5)
    clean_axis(ax_client)

    section_header(
        fig,
        gs[5, :],
        3,
        "SALES BY PRODUCT CATEGORY  ·  ORDERED BY PRODUCT COUNT",
    )

    order = category.sort_values(["models", "revenue"], ascending=[True, True]).index
    cat_gs = gs[6, :].subgridspec(1, 3, wspace=0.42)
    build_category_panel(
        fig.add_subplot(cat_gs[0, 0]),
        category,
        order,
        "models",
        "Products by category",
        "Number of products",
        NAVY,
        lambda value: f"{int(value)} ({value / overview['total_products'] * 100:.0f}%)",
    )
    build_category_panel(
        fig.add_subplot(cat_gs[0, 1]),
        category,
        order,
        "units",
        "Units sold by category",
        "Units sold",
        TEAL,
        lambda value: f"{int(value):,}",
    )
    category_millions = category.copy()
    category_millions["revenue_millions"] = category_millions["revenue"] / 1_000_000
    build_category_panel(
        fig.add_subplot(cat_gs[0, 2]),
        category_millions,
        order,
        "revenue_millions",
        "Revenue by category",
        "Revenue (₱ million)",
        AMBER,
        lambda value: f"₱{value:,.0f}M",
    )

    section_header(fig, gs[7, :], 4, "INVENTORY  ·  PRODUCTS, CATEGORIES, AND PRICING")

    inv_gs = gs[8, :].subgridspec(1, 2, wspace=0.22)
    inventory_table(fig.add_subplot(inv_gs[0, 0]), inventory.iloc[:25], 7.2)
    inventory_table(fig.add_subplot(inv_gs[0, 1]), inventory.iloc[25:], 7.2)

    footer = fig.add_subplot(gs[9, :])
    footer.axis("off")
    footer.text(
        0.0,
        0.68,
        "Source: data/cleaned/MotorPH_Product_List_Cleaned.csv and MotorPH_Sales_Cleaned.csv  |  "
        "Revenue = Quantity × Unit Price, reconciled to Total  |  "
        f"Analyzed: {overview['transactions']:,} transactions, {overview['total_units']:,} units, {peso_full(overview['total_revenue'])}",
        fontsize=7.4,
        color=GRAY,
        va="center",
    )
    footer.text(
        0.0,
        0.24,
        f"Data quality: {qa['sales_rows_loaded']:,} cleaned → {qa['sales_rows_analyzed']:,} analyzed "
        "(1 out-of-period excluded)  ·  0 missing  ·  0 duplicates  ·  0 unmatched  ·  "
        "0 price/revenue mismatches  |  Python 3.13.1  ·  pandas 3.0.6  ·  matplotlib 3.11.2",
        fontsize=7.2,
        color=GRAY,
        va="center",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(DASHBOARD_PNG, dpi=150, bbox_inches="tight", pad_inches=0.22, facecolor="white")
    plt.close(fig)


def build_inventory_figure(metrics):
    inventory = metrics["inventory"]
    overview = metrics["overview"]

    fig = plt.figure(figsize=(16, 10), facecolor="white")
    gs = GridSpec(
        1,
        2,
        figure=fig,
        wspace=0.18,
        left=0.03,
        right=0.97,
        top=0.84,
        bottom=0.08,
    )
    fig.text(
        0.5,
        0.95,
        "MotorPH Inventory  ·  Products, Categories, and Pricing",
        fontsize=18,
        fontweight="bold",
        color=NAVY,
        ha="center",
    )
    fig.text(
        0.5,
        0.905,
        f"All {overview['total_products']} products from the cleaned MotorPH product list  |  "
        "unit price and Q3 2025 sales for context",
        fontsize=9.5,
        color=GRAY,
        ha="center",
    )

    inventory_table(fig.add_subplot(gs[0, 0]), inventory.iloc[:25], 9.0)
    inventory_table(fig.add_subplot(gs[0, 1]), inventory.iloc[25:], 9.0)

    fig.text(
        0.5,
        0.035,
        f"TOTAL: {overview['total_products']} products  |  {overview['total_categories']} categories  |  "
        f"{overview['total_units']:,} units sold  |  {peso_full(overview['total_revenue'])} revenue",
        fontsize=9,
        color=NAVY,
        fontweight="bold",
        ha="center",
    )

    fig.savefig(INVENTORY_PNG, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_qa_file(metrics, qa):
    overview = metrics["overview"]
    heritage = metrics["heritage_trace"]
    category = metrics["category"]
    lines = [
        "MOTORPH MS2 - DATA QUALITY AND RECONCILIATION REPORT",
        "=" * 64,
        f"Products file: {PRODUCTS_FILE.name}",
        f"Sales file: {SALES_FILE.name}",
        "",
        "LOADED",
        f"  Product rows: {qa['products_rows']}",
        f"  Sales rows: {qa['sales_rows_loaded']}",
        f"  Sales rows analyzed: {qa['sales_rows_analyzed']}",
        f"  Date window: {qa['date_min']:%Y-%m-%d} to {qa['date_max']:%Y-%m-%d}",
        "",
        "QUALITY CHECKS",
        f"  Missing values (products / sales): {qa['missing_products']} / {qa['missing_sales']}",
        f"  Duplicate rows (products / sales): {qa['duplicate_products']} / {qa['duplicate_sales']}",
        f"  Unparseable dates: {qa['unparseable_dates']}",
        f"  Unmatched product names: {qa['unmatched_products']}",
        f"  Unit price mismatch vs product list: {qa['price_mismatch']}",
        f"  Quantity x Unit Price != Total: {qa['revenue_mismatch']}",
        f"  Out-of-period rows excluded: {qa['out_of_period']}",
    ]
    if qa["out_of_period"]:
        lines.append("  Excluded row(s):")
        for _, row in qa["out_of_period_rows"].iterrows():
            lines.append(
                f"    {row['Date']:%Y-%m-%d} | {row['Product']} | "
                f"{int(row['Quantity'])} units | {peso_full(row['Total'])}"
            )
    lines.extend(
        [
            "",
            "RECONCILIATION",
            f"  Total products: {overview['total_products']}",
            f"  Total categories: {overview['total_categories']}",
            f"  Total units: {overview['total_units']:,}",
            f"  Total revenue: {peso_full(overview['total_revenue'])}",
            f"  Transactions: {overview['transactions']:,}",
            f"  Average order value: {peso_full(overview['avg_order_value'])}",
            f"  Category revenue sum: {peso_full(category['revenue'].sum())}",
            f"  Monthly revenue sum: {peso_full(metrics['monthly']['revenue'].sum())}",
            "",
            "HERITAGE TRACE",
        ]
    )
    for product, row in heritage.iterrows():
        lines.append(
            f"  {product}: {int(row['units']):,} units | {peso_full(row['revenue'])}"
        )
    lines.extend(
        [
            "",
            "STATUS: PASS - all quality checks passed, revenue reconciled.",
            "=" * 64,
        ]
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    QA_FILE.write_text("\n".join(lines), encoding="utf-8")


def print_summary(metrics, qa):
    overview = metrics["overview"]
    print("MotorPH MS2 dashboard")
    print("-" * 60)
    print(f"Products: {overview['total_products']} | Categories: {overview['total_categories']}")
    print(
        f"Sales rows analyzed: {qa['sales_rows_analyzed']} "
        f"(out-of-period excluded: {qa['out_of_period']})"
    )
    print(
        f"Units: {overview['total_units']:,} | Revenue: {peso_full(overview['total_revenue'])} "
        f"| Transactions: {overview['transactions']:,}"
    )
    print(f"Quality gate: {'PASS' if qa['quality_ok'] else 'FAIL'}")
    print(f"Saved: {DASHBOARD_PNG.name}, {INVENTORY_PNG.name}, {QA_FILE.name}")


def main():
    products, sales = load_data()
    products, sales, qa = validate_and_filter(products, sales)
    metrics = compute_metrics(products, sales)
    write_qa_file(metrics, qa)
    build_dashboard(metrics, qa)
    build_inventory_figure(metrics)
    print_summary(metrics, qa)


if __name__ == "__main__":
    main()
