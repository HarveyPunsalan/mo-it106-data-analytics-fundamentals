# MotorPH product list and sales data (3rd quarter, year 2025)
# loading, checking and cleaning the two datasets before analysis

import pandas as pd


def summarize(df):
    # short look at a dataframe, used before and after cleaning
    print('shape:', df.shape)
    print('missing values:', df.isnull().sum().sum())
    print('duplicate rows:', df.duplicated().sum())
    print(df.dtypes)


# load the datasets downloaded from the MotorPH site
products = pd.read_csv('MotorPH_Products_List_2025.csv')
sales = pd.read_csv('MotorPH_Sales Data-3rd Quarter-Year 2025.csv')


# ---------------------------------------------------------------
# 1. check the product list
# ---------------------------------------------------------------
print('PRODUCT LIST')
print(products.head())
summarize(products)

# the data itself is complete: IDs run from 1 to 50, no blanks, no duplicates.
# the problems are in the columns:
#   - the names are hard to understand (EntrNo, EntrName) and Acquisiton is misspelled
#   - EntrDetails mixes the category and the specs, e.g. "Sport / Parallel-twin, ... 471cc"
#   - Manufacturing Date and Acquisiton only hold a year, not a real date
print('IDs:', products['EntrNo'].tolist())
print(products['EntrDetails'].head())
print('categories found:', sorted(products['EntrDetails'].str.split('/').str[0].str.strip().unique()))


# ---------------------------------------------------------------
# 2. check the sales data
# ---------------------------------------------------------------
print('SALES DATA')
print(sales.head())
summarize(sales)

# date, client_type and payment have blank values
print(sales.isnull().sum())

# there are no exact duplicate rows, but some records repeat the same sale
print('same date, product, quantity and total:',
      sales.duplicated(subset=['date', 'product', 'quantity', 'total']).sum())

# the dates are not written the same way and some are not real dates at all
print(sorted(sales['date'].dropna().unique())[:12])

# the categories are readable but they are plain text
print(sales['client_type'].value_counts())
print(sales['payment'].value_counts())

# some product names here do not exist in the product list (typos)
print(sorted(set(sales['product']) - set(products['EntrName'])))

# and the unit price does not always match the price in the product list
list_price = sales['product'].map(dict(zip(products['EntrName'], products['UnitPrice'])))
found = sales['product'].isin(products['EntrName'])
print('rows with a price that does not match the product list:',
      (sales.loc[found, 'unitprice'] != list_price[found]).sum())
print('rows where unitprice x quantity is not the total:',
      (sales['unitprice'] * sales['quantity'] != sales['total']).sum())


# ---------------------------------------------------------------
# 3. clean the product list
# ---------------------------------------------------------------
# rename the columns so the report is clear to read
products = products.rename(columns={
    'EntrNo': 'Product ID Number',
    'EntrName': 'Product Name',
    'EntrDetails': 'Product Category',
    'Manufacturing Date': 'Manufacturing Year',
    'Acquisiton': 'Acquisition Year',
    'UnitPrice': 'Unit Price',
})

# EntrDetails packs the category and the specs together, so keep the category
# only and drop the specs
products['Product Category'] = products['Product Category'].str.split('/').str[0].str.strip()
products['Product Name'] = products['Product Name'].str.strip()

# the ID, the years and the price are already stored as whole numbers so there
# is nothing to convert, let me just put the columns in the report order
products = products[['Product ID Number', 'Product Name', 'Product Category',
                     'Manufacturing Year', 'Acquisition Year', 'Unit Price']]


# ---------------------------------------------------------------
# 4. clean the sales data
# ---------------------------------------------------------------
sales = sales.rename(columns={
    'date': 'Date',
    'client_type': 'Client Type',
    'product': 'Product',
    'unitprice': 'Unit Price',
    'quantity': 'Quantity',
    'total': 'Total',
    'payment': 'Payment',
})

# trim the spaces in the text columns
for col in ['Client Type', 'Product', 'Payment']:
    sales[col] = sales[col].str.strip()

# the last letter of these product names was replaced with an x
clean_names = {
    'Bajaj CT12x': 'Bajaj CT125',
    'Benelli 502x': 'Benelli 502C',
    'Bristol Bobber 65x': 'Bristol Bobber 650',
    'CFMoto 300Sx': 'CFMoto 300SR',
    'Honda ADV 16x': 'Honda ADV 160',
    'KTM 790 Dukx': 'KTM 790 Duke',
    'Kawasaki KLX 23x': 'Kawasaki KLX 230',
    'Motorstar Xplorer 250x': 'Motorstar Xplorer 250R',
    'Suzuki Raider R150 Fx': 'Suzuki Raider R150 Fi',
    'TVS Apache RTR 200 4x': 'TVS Apache RTR 200 4V',
    'Yamaha MT-1x': 'Yamaha MT-15',
    'Yamaha Serow 25x': 'Yamaha Serow 250',
    'Yamaha Sniper 15x': 'Yamaha Sniper 155',
}
sales['Product'] = sales['Product'].replace(clean_names)

# the dates are written in different ways so I try one format at a time and
# keep whatever came out
raw_date = sales['Date']
sales['Date'] = pd.NaT
for fmt in ['%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
            '%Y/%m/%d', '%Y-%m-%d', '%b-%d-%Y', '%d/%m/%Y']:
    sales['Date'] = sales['Date'].fillna(
        pd.to_datetime(raw_date, format=fmt, errors='coerce'))

# 2 rows have no date and 4 rows have an impossible date (day 32, day 40, day 00)
# so they cannot be used for analysis
print('dates that could not be read:', sales['Date'].isnull().sum())
sales = sales.dropna(subset=['Date'])

# the price in the product list is the correct one, follow that
sales['Unit Price'] = sales['Product'].map(
    dict(zip(products['Product Name'], products['Unit Price'])))

# fill in the blank client type and payment instead of removing the sale
sales['Client Type'] = sales['Client Type'].fillna('Unknown')
sales['Payment'] = sales['Payment'].fillna('Unknown')

# remove the repeated records, keeping the first one
sales = sales.drop_duplicates(subset=['Date', 'Product', 'Quantity', 'Total'])


# ---------------------------------------------------------------
# 5. check both datasets again after cleaning
# ---------------------------------------------------------------
print('PRODUCT LIST AFTER CLEANING')
summarize(products)
print('IDs are in order:', products['Product ID Number'].tolist() == list(range(1, 51)))
print('years:', sorted(products['Manufacturing Year'].unique()),
      sorted(products['Acquisition Year'].unique()))
print(products.head())

print('SALES DATA AFTER CLEANING')
summarize(sales)
print('all product names are in the product list:',
      sales['Product'].isin(products['Product Name']).all())
print('price x quantity is the total:',
      (sales['Unit Price'] * sales['Quantity'] == sales['Total']).all())
print(sales.head())


# ---------------------------------------------------------------
# 6. save the cleaned datasets
# ---------------------------------------------------------------
products.to_csv('MotorPH_Product_List_Cleaned.csv', index=False)
sales.to_csv('MotorPH_Sales_Cleaned.csv', index=False)
print('saved MotorPH_Product_List_Report.csv and MotorPH_Sales_Cleaned.csv')
