import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.title("🐱 Cat Data Entry")

# File handling options
st.header("📁 Data File Option")
file_option = st.radio(
    "Choose an option:",
    ["Create new file", "Upload existing file"],
    horizontal=True
)

# Column headers matching the original CSV structure
columns = ["Sample ID", "Date", "City", "Clinic", "Owner ID", "Age", "Age Group", "Sex", "Indoor/Outdoor", "Ticks", "Organ", "Number", "Size"]

data_file = "cat_data.xlsx" if file_option == "Create new file" else "cat_data.csv"

if file_option == "Upload existing file":
    uploaded_file = st.file_uploader("Upload Excel or CSV file", type=["xlsx", "csv"])
    if uploaded_file is not None:
        # Determine file type and read accordingly
        if uploaded_file.name.endswith(".xlsx"):
            try:
                uploaded_df = pd.read_excel(uploaded_file)
                data_file = "cat_data_uploaded.xlsx"
                uploaded_df.to_excel(data_file, index=False)
                st.success(f"Loaded: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")
                uploaded_df = None
        else:  # CSV
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                data_file = "cat_data_uploaded.csv"
                uploaded_df.to_csv(data_file, index=False)
                st.success(f"Loaded: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
                uploaded_df = None
    else:
        st.info("Please upload a file or choose 'Create new file'")

# Data entry form
st.header("📝 Enter Cat Data")

with st.form("data_form"):
    sample_id = st.text_input("Sample ID")
    city = st.text_input("City")
    clinic = st.text_input("Clinic")
    owner = st.text_input("Owner ID")
    age = st.number_input("Cat Age", min_value=0.0)

    age_group = st.selectbox("Age Group", ["Kitten","Young","Adult"])
    sex = st.selectbox("Sex", ["M","F"])
    indoor = st.selectbox("Indoor/Outdoor", ["Indoor","Outdoor"])

    ticks = st.selectbox("Ticks Presence", ["Positive","Negative"])

    organ = number = size = ""

    if ticks == "Positive":
        organ = st.text_input("Organ of Tick")
        number = st.text_input("Number of Ticks")
        size = st.text_input("Size of Ticks")

    submit = st.form_submit_button("Save Data")

if submit:
    row = {
        "Sample ID": sample_id,
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "City": city,
        "Clinic": clinic,
        "Owner ID": owner,
        "Age": age,
        "Age Group": age_group,
        "Sex": sex,
        "Indoor/Outdoor": indoor,
        "Ticks": ticks,
        "Organ": organ,
        "Number": number,
        "Size": size
    }

    df = pd.DataFrame([row])

    # Save based on file type
    if data_file.endswith(".xlsx"):
        if os.path.exists(data_file):
            # Append to existing Excel file
            existing_df = pd.read_excel(data_file)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_excel(data_file, index=False)
        else:
            df.to_excel(data_file, index=False)
    else:
        # CSV file
        if os.path.exists(data_file):
            df.to_csv(data_file, mode='a', header=False, index=False)
        else:
            df.to_csv(data_file, index=False)

    st.success(f"Data saved to {data_file}!")

# Display current data
if os.path.exists(data_file):
    st.header("📊 Current Data")
    if data_file.endswith(".xlsx"):
        display_df = pd.read_excel(data_file)
    else:
        display_df = pd.read_csv(data_file)
    st.dataframe(display_df)
