import streamlit as st
import pandas as pd
import re
from datetime import datetime
import plotly.express as px

def parse_whatsapp_chat(content):
    lines = content.split('\n')
    messages = []
    current_message = []
    date_pattern = r'^\d{2}/\d{2}/\d{2},\s+\d{1,2}:\d{2}\s+(am|pm)\s+-'

    for line in lines:
        if re.match(date_pattern, line):
            if current_message:
                full_message = ' '.join(current_message).strip()
                try:
                    date_time, name_message = full_message.split(' - ', 1)
                    date, time = date_time.split(', ')
                    if ': ' in name_message:
                        name, message = name_message.split(': ', 1)
                    else:
                        name = "System"
                        message = name_message
                    messages.append({'Date': date, 'Name': name, 'Message': message})
                except ValueError:
                    continue
                current_message = [line]
            else:
                current_message = [line]
        else:
            current_message.append(line)

    if current_message:
        full_message = ' '.join(current_message).strip()
        try:
            date_time, name_message = full_message.split(' - ', 1)
            date, time = date_time.split(', ')
            if ': ' in name_message:
                name, message = name_message.split(': ', 1)
            else:
                name = "System"
                message = name_message
            messages.append({'Date': date, 'Name': name, 'Message': message})
        except ValueError:
            pass

    return pd.DataFrame(messages)

def filter_messages(df, start_date, end_date):
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y')
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    return df.loc[mask]

def analyze_messages(df):
    total_messages = len(df)
    person_message_count = df['Name'].value_counts().to_frame('Total Messages')
    df['Is Media'] = df['Message'].apply(lambda x: 'Media' if '<Media omitted>' in x else 'Text')
    media_counts = df.pivot_table(index='Name', columns='Is Media', aggfunc='size', fill_value=0)
    month_wise_data = df.resample('M', on='Date')['Message'].count().reset_index()
    month_wise_data['Month'] = month_wise_data['Date'].dt.strftime('%Y-%m')
    return total_messages, person_message_count, media_counts, month_wise_data

# Streamlit app
st.title('WhatsApp Chat Analyzer')

uploaded_file = st.file_uploader("Choose a WhatsApp chat file", type="txt")
if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8")
    messages_df = parse_whatsapp_chat(content)

    st_date = st.text_input("Start Date (dd/mm/yyyy)")
    end_date = st.text_input("End Date (dd/mm/yyyy)")

    if st.button("Filter Messages"):
        if st_date and end_date:
            try:
                start_date = datetime.strptime(st_date, '%d/%m/%y')
                end_date = datetime.strptime(end_date, '%d/%m/%y')
                filtered_df = filter_messages(messages_df, start_date, end_date)
                
                total_messages, person_message_count, media_counts, month_wise_data = analyze_messages(filtered_df)
                st.subheader("Analysis Results")
                st.write("Total messages in this timeline:", total_messages)
                st.write("Person-wise total messages:", person_message_count)
                st.write("Breakdown of text and media messages:", media_counts)

                # Plotting month-wise message data
                fig = px.line(month_wise_data, x='Month', y='Message', title='Month-wise Message Counts', markers=True)
                st.plotly_chart(fig, use_container_width=True)
                
            except ValueError as e:
                st.error("Error in date format: " + str(e))
        else:
            st.error("Please enter both start and end dates.")
