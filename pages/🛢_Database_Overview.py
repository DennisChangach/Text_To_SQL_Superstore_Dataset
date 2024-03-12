import streamlit as st
import mysql.connector
import pandas as pd

import os
from dotenv import load_dotenv

load_dotenv()

st.title("SuperStore Database Overview")

st.markdown("""
        Tableau Superstore is a sample Dataset provided by Tableau.It includes data for the Sales of multiple products sold by a company 
        along with subsequent information related to the orders.""")

#Table selector
table_name = st.selectbox(
    "Choose a table from the database: showing the first 50 rows",
    ('orders','returns','people'))


#Using the Try Catch
try:
    #Connecting to the Database
    connection = mysql.connector.connect(
    host=os.environ["db_host"],
    user=os.environ["db_user"],
    password=os.environ["db_password"],
    database=os.environ["db_name"]
)
    # Create a cursor object to interact with the database
    cursor = connection.cursor()

    # Define the SQL query you want to execute
    query = f"SELECT * FROM {table_name} LIMIT 50"

    # Execute the query
    cursor.execute(query)

    # Fetch all the rows returned by the query
    rows = cursor.fetchall()

    # Get column names from the cursor description
    column_names = [desc[0] for desc in cursor.description]

    # Close the cursor
    cursor.close()

    # Close the connection
    connection.close()

    # Convert the fetched rows into a DataFrame
    df = pd.DataFrame(rows, columns=column_names)

    # Print the DataFrame
    st.dataframe(df)
    
except Exception as e:
    st.write("⚠️ Sorry, Couldn't establish a connection to the Database")