import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# Read CSV file
df = pd.read_csv("data/earthquakes_cleaned.csv")

# Encode password (safe even if no special chars)
password = quote_plus("12345")

# MySQL connection URL
mysql_url = f"mysql+pymysql://root:{password}@localhost:3306/b115_b118"

# Create engine
engine = create_engine(mysql_url)

# Write DataFrame to MySQL
df.to_sql(name="earthquakes_data",con=engine,
    if_exists="replace",  
    index=False
)

# Read data back from MySQL
result_df = pd.read_sql_table(table_name="earthquakes_data",con=engine)

print(result_df.head())
