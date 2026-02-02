import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURATION ---
# Replace this with your Google Sheet "Published CSV" link
# To get this: File > Share > Publish to Web > Link > CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQXqcR0QBwiJO_nTN9lf5PR9vP7Ps2Smuz8djDjo7s22or7-B_yoWy79NnEaJ1LWMkG2Elnc1mh1n0k/pubhtml"

st.set_page_config(page_title="Friend Tracker", layout="wide")

# --- 2. LOAD DATA ---
@st.cache_data(ttl=300)  # Refreshes every 5 minutes
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        # Ensure times are strings and padded (e.g., '9:00' becomes '09:00')
        data['Start'] = data['Start'].astype(str).str.zfill(5)
        data['End'] = data['End'].astype(str).str.zfill(5)
        return data
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return pd.DataFrame()

df = load_data()

# --- 3. CURRENT TIME LOGIC ---
now = datetime.now()
current_day = now.strftime("%A")
current_time = now.strftime("%H:%M")

# --- 4. THE LOGIC FUNCTION ---
def check_status(name_to_check, full_df):
    # Filter for the person and the day
    today_blocks = full_df[(full_df['Name'] == name_to_check) & (full_df['Day'] == current_day)]
    
    # Check every block for a match
    for _, row in today_blocks.iterrows():
        if row['Start'] <= current_time <= row['End']:
            return {
                "status": "Busy", 
                "activity": row['Activity'], 
                "until": row['End'],
                "location": row.get('Location', 'Unknown')
            }
    
    # If no blocks match, they are free
    return {"status": "Free"}

# --- 5. SIDEBAR: PERSONAL VIEW ---
st.sidebar.title("👤 Personal View")
if not df.empty:
    all_friends = sorted(df['Name'].unique())
    user_name = st.sidebar.selectbox("Who are you?", all_friends)
    
    personal_today = df[(df['Name'] == user_name) & (df['Day'] == current_day)].sort_values(by="Start")
    
    if not personal_today.empty:
        for _, row in personal_today.iterrows():
            st.sidebar.info(f"**{row['Start']} - {row['End']}**\n\n{row['Activity']} (@ {row['Location']})")
    else:
        st.sidebar.write("No scheduled blocks for you today!")

# --- 6. MAIN DASHBOARD ---
st.title
