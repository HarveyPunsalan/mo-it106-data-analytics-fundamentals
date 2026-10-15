# MotorPH product list - category distribution chart
# loads the cleaned product list and saves a bar chart
# used for the Milestone 2 draft

import pandas as pd
import matplotlib.pyplot as plt


def make_chart(df):
    # count how many products fall under each category, most first
    counts = df['Product Category'].value_counts()
    # share of each category out of all the products
    shares = counts / len(df) * 100

    # make the bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(counts.index, counts.values)

    # put the count and share on top of each bar so it is easy to read
    for i, (c, s) in enumerate(zip(counts.values, shares.values)):
        plt.text(i, c + 0.15, f'{c} ({s:.0f}%)', ha='center', fontsize=8)

    # title and labels
    plt.title('MotorPH Products by Category')
    plt.xlabel('Product Category')
    plt.ylabel('Number of Products')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # save the chart and show it
    plt.savefig('MotorPH_Category_Chart.png')
    print('saved MotorPH_Category_Chart.png')
    print(counts)


# load the cleaned product list from Milestone 1
df = pd.read_csv('MotorPH_Product_List_Cleaned.csv')
make_chart(df)
plt.show()
