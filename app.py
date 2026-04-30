import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.title("🐱 Cat Data Entry")

# Initialize session state for data
if 'data_df' not in st.session_state:
    st.session_state.data_df = pd.DataFrame(columns=[
        "Date", "Sample ID", "City", "Clinic", "Owner ID", "Age", 
        "Age Group", "Sex", "Indoor/Outdoor", "Ticks", "Organ", "Number", "Size"
    ])

# Initialize session state for uploaded data
if 'uploaded_data_df' not in st.session_state:
    st.session_state.uploaded_data_df = None

# Delete previous session CSV files at app startup
csv_files = ["cat_data.csv", "cat_data_uploaded.csv"]
for csv_file in csv_files:
    if os.path.exists(csv_file):
        try:
            os.remove(csv_file)
        except Exception as e:
            pass  # Ignore errors - file may be in use

# File handling options
st.header("📁 Data File Option")
file_option = st.radio(
    "Choose an option:",
    ["Create new file", "Upload existing file"],
    horizontal=True
)

data_file = "cat_data.csv"

# Store uploaded data separately in session state (preserves original uploaded data)
if file_option == "Upload existing file":
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            st.session_state.uploaded_data_df = pd.read_csv(uploaded_file)
            st.success(f"Loaded: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            st.session_state.uploaded_data_df = None
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

    # Add to session state (not persisted to CSV)
    new_row_df = pd.DataFrame([row])
    st.session_state.data_df = pd.concat([st.session_state.data_df, new_row_df], ignore_index=True)

    st.success("Data saved for current session!")

# Display current data
st.header("📊 Current Data")

# Show all data - merge uploaded data with session state data
display_df = st.session_state.data_df.copy()
if st.session_state.uploaded_data_df is not None:
    # Add uploaded data to existing session data (don't overwrite)
    display_df = pd.concat([display_df, st.session_state.uploaded_data_df], ignore_index=True)

if not display_df.empty:
    st.dataframe(display_df)
else:
    st.info("No data in current session. Upload a CSV file or enter new data above.")

# Download button for current session data (includes both entered and uploaded data)
if not display_df.empty:
    st.header("💾 Download Data")
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV File",
        data=csv,
        file_name="cat_data.csv",
        mime="text/csv"
    )
