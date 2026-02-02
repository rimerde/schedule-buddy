import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURATION ---
SHEET_URL = "YOUR_PUBLIC_GOOGLE_SHEET_CSV_LINK_HERE"

st.set_page_config(page_title="Friend Tracker", layout="wide")

# --- 2. LOAD DATA (ROBUST VERSION) ---
@st.cache_data(ttl=60) 
def load_data():
    try:
        # We read the CSV and tell it to ignore messy extra columns
        data = pd.read_csv(SHEET_URL, on_bad_lines='skip', engine='python')
        
        # CLEANING: Remove leading/trailing spaces from column names
        data.columns = data.columns.str.strip()
        
        # Check if the required column exists after cleaning
        if 'Start' not in data.columns:
            st.error(f"Column 'Start' not found. Available columns: {list(data.columns)}")
            return pd.DataFrame()

        # Ensure times are strings and padded (e.g., '9:00' -> '09:00')
        data['Start'] = data['Start'].astype(str).str.strip().str.zfill(5)
        data['End'] = data['End'].astype(str).str.strip().str.zfill(5)
        return data
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- 3. CURRENT TIME LOGIC ---
now = datetime.now()
current_day = now.strftime("%A")
current_time = now.strftime("%H:%M")

# --- 4. THE LOGIC FUNCTION ---
def check_status(name_to_check, full_df):
    today_blocks = full_df[(full_df['Name'] == name_to_check) & (full_df['Day'] == current_day)]
    
    for _, row in today_blocks.iterrows():
        # Using string comparison for 24-hour time
        if str(row['Start']) <= current_time <= str(row['End']):
            return {
                "status": "Busy", 
                "activity": row['Activity'], 
                "until": row['End'],
                "location": row.get('Location', 'Unknown')
            }
    return {"status": "Free"}

# --- 5. DASHBOARD DISPLAY ---
st.title("🤝 Group Schedule Tracker")

if not df.empty:
    friends = sorted(df['Name'].unique())
    
    # Personal View Sidebar
    user_name = st.sidebar.selectbox("Select Your Name", friends)
    st.sidebar.markdown(f"### Your {current_day} Schedule")
    my_sched = df[(df['Name'] == user_name) & (df['Day'] == current_day)].sort_values('Start')
    for _, r in my_sched.iterrows():
        st.sidebar.write(f"🕒 {r['Start']}-{r['End']}: {r['Activity']}")

    # Main Columns
    free_list, busy_list = [], []
    for name in friends:
        info = check_status(name, df)
        if info['status'] == "Busy":
            busy_list.append(f"🔴 **{name}**: {info['activity']} (until {info['until']})")
        else:
            # Look for next block
            future = df[(df['Name'] == name) & (df['Day'] == current_day) & (df['Start'] > current_time)]
            if not future.empty:
                next_t = future['Start'].min()
                free_list.append(f"🟢 **{name}**: Free until {next_t}")
            else:
                free_list.append(f"🟢 **{name}**: Free for the day! 🌴")

    col1, col2 = st.columns(2)
    with col1:
        st.header("Free Now")
        for item in free_list: st.write(item)
    with col2:
        st.header("Busy Now")
        for item in busy_list: st.write(item)

st.button("Manual Refresh", on_click=st.cache_data.clear)
