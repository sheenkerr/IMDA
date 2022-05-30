# Import required modules
import sqlite3
# importing pandas as pd
import pandas as pd

# Data Cleaning

# Load CSV data into Pandas DataFrame
df = pd.read_csv('ramen-ratings.csv')

country_df = pd.read_csv('Country-Codes.csv')

keys = list(country_df['Code'])
values = list(country_df['Country'])
map_values = dict(zip(keys, values))
mapper = df.Country.isin(map_values)
df.loc[mapper, 'Country'] = df.loc[mapper, 'Country'].apply(lambda row: map_values[row])

df["Complete"] = 1 # Create New Column called "Complete" to see if review is completed


for index, row in df.iterrows():
    if (pd.isna(row.Rating) or str(row.Rating) == "#VALUE!"):
        df.loc[index,"Complete"] = 0
        df.loc[index,"Rating"] = 0.00

# Replace NULL values with "Not Provided"
df = df.fillna("Not Provided")



del df["ID"] # Delete ID Column due to duplicate values

df["ID"] = df.index + 1 # Recreate the ID column with increments of 1 based on Index of DF

df = df.iloc[:, [6,0,1,2,3,4,5]] # Rearrange Columns to ensure ID is still the 1st Column

# Convert all values in Rating to Float
df = df.astype({"Rating":"float"})
#=============================================================================================================
# Connecting to the geeks database
connection = sqlite3.connect("ramenReviews.db")

# Creating a cursor object to execute
# SQL queries on a database table
cursor = connection.cursor()

# Table Definition
create_table = """CREATE TABLE  if not exists ramenReviews(
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				Country VARCHAR NOT NULL,
                Brand VARCHAR NOT NULL,	
                Type VARCHAR NOT NULL,
                Package VARCHAR NOT NULL,
				Rating FLOAT NOT NULL,
                Complete INTEGER(1) NOT NULL
                );
				"""

# Creating the table into the database
cursor.execute(create_table)

 
# Write the data to a sqlite db table
df.to_sql('ramenReviews', connection, if_exists='replace', index=False)
   

# SQL query to retrieve all data from
# the person table To verify that the
# data of the csv file has been successfully
# inserted into the table
select_all = "SELECT * FROM ramenReviews"
rows = cursor.execute(select_all).fetchall()

# Output to the console screen
for r in rows:
    print(r)

# Committing the changes
connection.commit()

# closing the database connection
connection.close()
