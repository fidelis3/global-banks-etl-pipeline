
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3

import requests

URL = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attributes = ['Name', 'MC_USD_Billion']
csv_path = 'largest_banks.csv'
db_name = 'Banks.db'
table_name = 'Largest_banks'



def log_progress(message):
    timestamp_format = '%Y-%h-%d-%H:%M:%S'
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    with open("etl_project_log.txt", "a") as f:
        f.write(timestamp + ' : ' + message + '\n')
        


        

def extract(url, table_attributes):
    page = requests.get(url).text
    data = BeautifulSoup(page, "html.parser")
    df = pd.DataFrame(columns=table_attributes)
    tables = data.find_all('tbody')
    rows = tables[0].find_all('tr')
    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            data_dict = {
                "Name": col[1].find_all('a')[1].contents[0],
                "MC_USD_Billion": float(col[2].contents[0][:-1])  # strip '\n', cast to float
            }
            df1 = pd.DataFrame(data_dict, index=[0])
            df = pd.concat([df, df1], ignore_index=True)
    return df



# LOGS OF EXTRACTION
log_progress("ETL Job Started")
log_progress("Extract phase Started")
df = extract(URL, table_attributes)
print("Extracted Data:")
print(df)
log_progress("Extract phase Ended")

#TRANSFORMATION
def transform(df):
    # Step 1: Read exchange rate CSV and convert to dictionary
    exchange_rate = pd.read_csv('exchange_rate.csv', index_col=0).to_dict()['Rate']
    
    # Step 2: Add 3 new columns scaled by exchange rate, rounded to 2 decimal places
    
    # GBP column (sample provided in instructions)
    gbp_rate = float(exchange_rate['GBP'])
    df['MC_GBP_Billion'] = [np.round(x * gbp_rate, 2) for x in df['MC_USD_Billion']]
    
    # EUR column
    eur_rate = float(exchange_rate['EUR'])
    df['MC_EUR_Billion'] = [np.round(x * eur_rate, 2) for x in df['MC_USD_Billion']]
    
    # INR column
    inr_rate = float(exchange_rate['INR'])
    df['MC_INR_Billion'] = [np.round(x * inr_rate, 2) for x in df['MC_USD_Billion']]
    
   
    
    return df


#LOGS OF TRANSFORMATION
log_progress("Transform phase Started")
df = transform(df)
print("\nTransformed Data:")
print(df)
print(df['MC_EUR_Billion'][4])
log_progress("Transform phase Ended")


##LOAD TO CSV
def load_to_csv(df, csv_path):
    df.to_csv(csv_path, index=False)

log_progress("Load phase Started")
load_to_csv(df, csv_path)
log_progress("Load phase Ended")


##LOAD TO SQL
def load_to_sql(df, db_name, table_name):
    conn = sqlite3.connect(db_name)
    query_statement1=f'SELECT * FROM Largest_banks'
    query_output1=pd.read_sql_query(query_statement1, conn)
    print(query_output1)
    
    query_statement2=f"SELECT AVG(MC_GBP_Billion) FROM Largest_banks"
    query_output2=pd.read_sql_query(query_statement2, conn)
    print(query_output2)
    
    query_statement3=f'SELECT Name FROM Largest_banks LIMIT 5'
    query_output3=pd.read_sql_query(query_statement3, conn)
    print(query_output3)

    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
    
##LOGS OF LOAD TO SQL
log_progress("Load to SQL phase Started")
load_to_sql(df, db_name, table_name)
log_progress("Load to SQL phase Ended")    
