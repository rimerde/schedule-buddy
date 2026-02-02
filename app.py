import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIG ---
# Replace this with your Google Sheet "Public CSV" link or use st.connection
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQXqcR0QBwiJO_nTN9lf5PR9vP7Ps2Smuz8djDjo7s22or7-B_yoWy79NnEaJ1LWMkG2Elnc1mh1n0k/pub?output=csv"

st.title("🤝 Group Schedule Tracker")

# 1. Get Current Time/Day
now = datetime.now()
current_day = now.strftime("%A") # e.g., "Monday"
current_time = now.strftime("%H:%M")

st.write(f"**Current Time:** {current_day}, {current_time}")

# 2. Load Data
# For simplicity, we assume you've shared the sheet as a CSV link
@st.cache_data(ttl=10) # Refresh data every 10 seconds
def load_data():
    return pd.read_csv(SHEET_URL)

df = load_data()

# 3. Logic: Who is busy RIGHT NOW?
# 1. The Fixed Function (place this before the loop)
def check_status(name_to_check, full_df):
    # Filter for the specific person AND the specific day
    today_blocks = full_df[(full_df['Name'] == name_to_check) & (full_df['Day'] == current_day)]
    
    for _, row in today_blocks.iterrows():
        # Check if current time is within this specific block
        if str(row['Start']) <= current_time <= str(row['End']):
            return {
                "status": "Busy", 
                "activity": row['Activity'], 
                "until": row['End'],
                "location": row.get('Location', 'N/A')
            }
    return {"status": "Free"}

# 2. The Fixed Loop
friends = df['Name'].unique()
free_list = []
busy_list = []

for name in friends:
    # FIX: Pass the 'name' string and the 'df' DataFrame correctly
    status_info = check_status(name, df)
    
    if status_info['status'] == "Busy":
        busy_list.append(f"🔴 **{name}**: {status_info['activity']} (until {status_info['until']})")
    else:
        # Check for their next upcoming block
        future_blocks = df[(df['Name'] == name) & (df['Day'] == current_day) & (df['Start'] > current_time)]
        if not future_blocks.empty:
            next_start = future_blocks['Start'].min()
            free_list.append(f"🟢 **{name}**: Free until {next_start}")
        else:
            free_list.append(f"🟢 **{name}**: Free for the day! 🌴")

# Group by name and check everyone
friends = df['Name'].unique()
free_list = []
busy_list = []

for name in friends:
    status_info = check_status(df[df['Name'] == name])
    if status_info['status'] == "Busy":
        busy_list.append(f"🔴 **{name}**: {status_info['activity']} (until {status_info['until']})")
    else:
        free_list.append(f"🟢 **{name}**: Free right now")

# 4. Dashboard Display
col1, col2 = st.columns(2)

with col1:
    st.header("Free")
    for item in free_list:
        st.write(item)

with col2:
    st.header("Busy")
    for item in busy_list:
        st.write(item)
