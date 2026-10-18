# MotorPH product list - category distribution chart
# loads the cleaned product list and sales data, saves the charts
# used for the Milestone 2 submission

import pandas as pd
import matplotlib.pyplot as plt


def make_chart(products, sales):
    # count how many products fall under each category, most first
    counts = products['Product Category'].value_counts()
    # share of each category out of all the products
    shares = counts / len(products) * 100

    # attach the category to each sale, then total the units per category
    merged = sales.merge(
        products[['Product Name', 'Product Category']],
        left_on='Product', right_on='Product Name', how='left')
    units = merged.groupby('Product Category')['Quantity'].sum()
    units = units.reindex(counts.index)

    # make two charts stacked in one image
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    # top chart: product count per category
    ax1.bar(counts.index, counts.values)
    # put the count and share on top of each bar so it is easy to read
    for i, (c, s) in enumerate(zip(counts.values, shares.values)):
        ax1.text(i, c + 0.15, f'{c} ({s:.0f}%)', ha='center', fontsize=8)
    ax1.set_title('MotorPH Products by Category')
    ax1.set_xlabel('Product Category')
    ax1.set_ylabel('Number of Products')
    for label in ax1.get_xticklabels():
        label.set_rotation(45)
        label.set_ha('right')

    # bottom chart: units sold per category
    ax2.bar(units.index, units.values)
    # put the units sold on top of each bar so it is easy to read
    for i, u in enumerate(units.values):
        ax2.text(i, u + 40, f'{u:,}', ha='center', fontsize=8)
    ax2.set_title('MotorPH Units Sold by Category')
    ax2.set_xlabel('Product Category')
    ax2.set_ylabel('Units Sold')
    for label in ax2.get_xticklabels():
        label.set_rotation(45)
        label.set_ha('right')

    fig.tight_layout()

    # save the charts and show them
    fig.savefig('MotorPH_Category_Chart.png')
    print('saved MotorPH_Category_Chart.png')
    print(counts)
    print(units)


# load the cleaned product list and sales data from Milestone 1
products = pd.read_csv('MotorPH_Product_List_Cleaned.csv')
sales = pd.read_csv('MotorPH_Sales_Cleaned.csv')
make_chart(products, sales)
plt.show()
