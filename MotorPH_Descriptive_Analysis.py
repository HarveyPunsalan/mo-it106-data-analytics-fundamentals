# MotorPH product list - descriptive analysis
# loads the raw product list, cleans it, and prints the numbers
# used in the Milestone 1 report

import pandas as pd

# load the product list downloaded from the MotorPH site
df = pd.read_csv('MotorPH_Products_List_2025.csv')

# rename the columns to the report names and fix the misspelled header
df = df.rename(columns={
    'EntrNo': 'Product ID Number',
    'EntrName': 'Product Name',
    'EntrDetails': 'Product Category',
    'Manufacturing Date': 'Manufacturing Year',
    'Acquisiton': 'Acquisition Year',
    'UnitPrice': 'Unit Price',
})

# the details column packs the category and the specs, keep the category only
df['Product Category'] = df['Product Category'].str.split('/').str[0].str.strip()
df['Product Name'] = df['Product Name'].str.strip()

# check the data before analyzing
print('missing values:', df.isnull().sum().sum())
print('duplicate rows:', df.duplicated().sum())
print()

# 3.a total number of products
print('Total number of products:', len(df))
print()

# 3.b counts by product type
print(df['Product Category'].value_counts())
print()

# 3.c unit price statistics
print('Average (mean) price:', format(df['Unit Price'].mean(), ',.2f'))
print('Cheapest price:', format(df['Unit Price'].min(), ','), '-', df.loc[df['Unit Price'].idxmin(), 'Product Name'])
print('Most expensive price:', format(df['Unit Price'].max(), ','), '-', df.loc[df['Unit Price'].idxmax(), 'Product Name'])
print()

# 3.d total inventory cost
print('Total inventory cost:', format(df['Unit Price'].sum(), ','))
print()

# acquisitions per year, used in the observations
print(df['Acquisition Year'].value_counts().sort_index())
