from langchain.llms import GooglePalm
from langchain.utilities import SQLDatabase #connecting to SQL database
from langchain_experimental.sql import SQLDatabaseChain
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS #vector embeddngs
from langchain.prompts import SemanticSimilarityExampleSelector
from langchain.prompts import FewShotPromptTemplate
from langchain.chains.sql_database.prompt import PROMPT_SUFFIX, _mysql_prompt
from langchain.prompts.prompt import PromptTemplate
from dotenv import load_dotenv

from few_shots import few_shots
from decimal import Decimal
import pandas as pd

import os
import re
import ast

load_dotenv()

#Initializing the LLM
llm=GooglePalm(google_api_key=os.environ['GOOGLE_API_KEY'],temperature=0.6)

#Function to retrieve the define the query and retrieve the result from the DB
def get_few_shot_db_chain():
    #loading g the llm
    llm=GooglePalm(google_api_key=os.environ['GOOGLE_API_KEY'],temperature=0.6)

    #Connecting to the MySQL Database on Local
    #db_password: /Do Not Use Special Characters/
    db_user = "root"
    db_password = "root1234"
    db_host = "localhost"
    db_name = "sample_superstore"

    db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",sample_rows_in_table_info=3)

    #Embeddings
    embeddings=GoogleGenerativeAIEmbeddings(model='models/embedding-001')
    # creating a blob of all the sentences
    to_vectorize = [" ".join(example.values()) for example in few_shots]
    #generating a vector store: 
    vector_store=FAISS.from_texts(to_vectorize, embeddings, metadatas=few_shots)
    #example selector to check sematic similarity
    example_selector = SemanticSimilarityExampleSelector(
        vectorstore = vector_store,
        k=2, #number of examples
    )

    #Prompt prefix
    mysql_prompt = """You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
    Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
    Pay attention to use CURDATE() function to get the current date, if the question involves "today".
    For results with decimals, round off the numbers to 2 decimal places unless specified otherwise by the user.
    Use the following format:

    Question: Question here
    SQLQuery: SQL Query to run
    SQLResult: Result of the SQLQuery
    
    No pre-amble.
    """

    #Example prompt format
    example_prompt = PromptTemplate(
        input_variables=["Question", "SQLQuery", "SQLResult"],
        template="\nQuestion: {Question}\nSQLQuery: {SQLQuery}\nSQLResult: {SQLResult}",
    )
    # Entire Prompt
    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix=mysql_prompt,
        suffix=PROMPT_SUFFIX,
        input_variables=["input", "table_info", "top_k"], #These variables are used in the prefix and suffix
    )

    #Chain_
    chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, prompt=few_shot_prompt,return_direct=True,return_intermediate_steps=True)

    return chain


#defining a function to get the column names ans takes in the response as the input
def get_column_names(response):
    #Getting the sql cmd from the chain reponse
    sql_cmd = response['intermediate_steps'][2]['sql_cmd']

    #Using the llm to extract the name of the columns from the sql query
    column_names = llm.invoke("Could you generate the column names based on this SQL Query {} and store in a list called column_names".format(sql_cmd))

    # Define the regex pattern to match the list
    pattern = r"\[.*?\]"

    # Use re.search to find the first occurrence of the pattern
    match = re.search(pattern, column_names)

    if match:
        # Extract the matched substring
        extracted_list_str = match.group()
        # Parse the string representation of the list into a Python list
        extracted_list = ast.literal_eval(extracted_list_str)
        return extracted_list
    else:
        return None

#Function to return dataframe
def get_df(response):
    #Getting the SQL Command Generated
    column_names = get_column_names(response)

    result_list = eval(response['result'])
    df = pd.DataFrame(result_list,columns=column_names)
    return df
