import pandas as pd

def add_year_month_columns(df_transactions):
    df_transactions['purchase_date']=pd.to_datetime(df_transactions['purchase_date'], errors='coerce')
    df_transactions['sale_date']=pd.to_datetime(df_transactions['sale_date'], errors='coerce')
    df_transactions['purchase year'] = df_transactions['purchase_date'].dt.year
    df_transactions['purchase month'] = df_transactions['purchase_date'].dt.month
    df_transactions['purchase year_month'] = df_transactions['purchase_date'].dt.strftime('%Y-%m')
    df_transactions['sale year'] = df_transactions['sale_date'].dt.year
    df_transactions['sale month'] = df_transactions['sale_date'].dt.month
    df_transactions['sale year_month'] = df_transactions['sale_date'].dt.strftime('%Y-%m')


def all_time_report(df_transactions):

        add_year_month_columns(df_transactions)
        df_purchase = df_transactions.copy()
        df_purchase = df_purchase.groupby(['purchase year_month']).agg({'purchase_price_euro': 'sum'}).reset_index()
        df_purchase = df_purchase.rename(columns={'purchase year_month': 'year_month'})
        df_sale = df_transactions.copy()
        df_sale = df_sale[~df_sale['sale_date'].isnull()]
        df_sale = df_sale.groupby(['sale year_month']).agg(
            {'sale_price_eur': 'sum', 'earnings_eur': 'sum','sale_price' : 'sum'}).reset_index()
        df_sale = df_sale.rename(columns={'sale year_month': 'year_month'})
        df_monthly = df_sale.merge(df_purchase, on=['year_month'], how='outer')
        df_monthly = df_monthly.sort_values(['year_month'])

        df_monthly=df_monthly.rename(columns={'year_month':'month','sale_price_eur':'Sales (EUR)','purchase_price_euro':'Purchases (EUR)','sale_price':'Sales (kRUB)','earnings_eur':'Earnings (EUR)'})
        df_monthly=df_monthly[['month','Purchases (EUR)','Sales (kRUB)','Sales (EUR)','Earnings (EUR)']]
        df_monthly=df_monthly.sort_values('month',ascending=False)
        df_monthly['Sales (kRUB)']=df_monthly['Sales (kRUB)']/1000
        df_monthly['Premium %']=(df_monthly['Earnings (EUR)']/(df_monthly['Sales (EUR)']-df_monthly['Earnings (EUR)'])*100.)
        df_monthly = df_monthly.fillna(0.)
        df_monthly['Premium %']=df_monthly['Premium %'].astype('int')

        return df_monthly
