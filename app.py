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

data_file = "cat_data.csv"

if file_option == "Upload existing file":
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
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

with st.form("data_form", clear_on_submit=True):
    sample_id = st.text_input("Sample ID")
    city = st.text_input("City")
    clinic = st.text_input("Clinic")
    owner = st.text_input("Owner ID")
    age = st.number_input("Cat Age", min_value=0, step=1, format="%d")

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
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Sample ID": sample_id,
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

    # CSV file handling
    if os.path.exists(data_file):
        df.to_csv(data_file, mode='a', header=False, index=False)
    else:
        df.to_csv(data_file, index=False)

    st.success(f"Data saved to {data_file}!")
    st.rerun()

# Download button for CSV file
if os.path.exists(data_file):
    st.header("💾 Download Data")
    with open(data_file, "rb") as file:
        st.download_button(
            label="📥 Download CSV File",
            data=file,
            file_name="cat_data.csv",
            mime="text/csv"
        )

# Display current data
if os.path.exists(data_file):
    st.header("📊 Current Data")
    display_df = pd.read_csv(data_file)
    st.dataframe(display_df)
