import streamlit as st
import pandas as pd
from sql_generator import get_few_shot_db_chain
from sql_generator import get_df


#The Main Function
def main():

    st.set_page_config(page_title="Text To SQL",page_icon="")
    st.title("SuperStore Database Q&A 🏪")

    #Chat Window
    
    with st.chat_message("assistant"):
        st.write("Please go ahead and Query your Database: e.g. What are the top 5 sub-categories with the highest sales?")
    
    #Initializing Mwessage history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    #Display the session history
    if len(st.session_state.messages) !=0:
        #Displaying chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                #priting the questions
                if 'question' in message:
                    st.markdown(message["question"])
                #printing the sql code
                elif 'sql' in message:
                    st.code(message["sql"])
                #retrieving the dictionary and converting back to df
                elif 'df' in message:
                    new_df = pd.DataFrame(message['df'])
                    st.dataframe(new_df)
                #retrieving error messages
                elif 'error' in message:
                    st.text(message['error'])


    
    #Getting the user's input
    user_question = st.chat_input("Ask your Database")
    #Checking if the user has input  a message
    if user_question:
        #Displaying the user question in the chat message
        with st.chat_message("user"):
            st.markdown(user_question)
        #Adding user question to chat history
        st.session_state.messages.append({"role":"user","question":user_question})
        try:
            chain = get_few_shot_db_chain()
            #Getting the response
            response = chain(user_question)

            #Get the table from the results
            df = get_df(response)
            # Storing the DataFrame in the session state
            #Retrieving the SQL Code to Run
            sql_cmd = response['intermediate_steps'][2]['sql_cmd']

            #Displyaing the assistant response
            with st.chat_message("assistant"):
                st.code(sql_cmd)
                st.dataframe(df)
            
            #Creating a dictionary to store the dataframe
            df_dict = df.to_dict(orient='records')
            
            #Adding the assistant response to chat history
            st.session_state.messages.append({"role":"assistant","sql":sql_cmd})
            #Adding the dataframe to the dataframe history
            st.session_state.messages.append({"role":"assistant","df":df_dict})
            #st.write(st.session_state.messages)


        except Exception as e:
            #st.write(e)
            error_message = "⚠️ Sorry, Couldn't generate the SQL Query! Please try rephrasing your question"
            #Displaying the error message
            with st.chat_message("assistant"):  
                st.text(error_message)

            #Appending the error messaage to the session
            st.session_state.messages.append({"role":"assistant","error":error_message})

    
    
    #Side Menu Bar
    with st.sidebar:
        st.title("Configuration:⚙️")
        st.write("Check the Database Overview tab to learn more about the data and the possible questions you may want answered!")

        
        



    
    #Function to clear history
    def clear_chat_history():
        st.session_state.messages = []
    #Button for clearing history
    st.sidebar.button("Clear Chat History",on_click=clear_chat_history)

    
    
    #Button


#Running the File
if __name__ == "__main__":
    main()