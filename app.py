import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQXqcR0QBwiJO_nTN9lf5PR9vP7Ps2Smuz8djDjo7s22or7-B_yoWy79NnEaJ1LWMkG2Elnc1mh1n0k/pub?output=csv"

st.set_page_config(page_title="Friend Tracker", layout="wide")

# --- 2. LOAD DATA (ROBUST VERSION) ---
@st.cache_data(ttl=60) 
def load_data():
    try:
        # Load the CSV
        data = pd.read_csv(SHEET_URL, on_bad_lines='skip', engine='python')
        
        # CLEANING: Remove hidden spaces from column headers
        data.columns = data.columns.str.strip()
        
        # SAFETY CHECK: If 'Name' is missing, show a helpful error instead of crashing
        if 'Name' not in data.columns:
            st.error(f"⚠️ 'Name' column not found! I see: {list(data.columns)}")
            return pd.DataFrame() # Return empty table

        # Clean the actual data
        data = data.dropna(subset=['Name'])
        data['Name'] = data['Name'].astype(str).str.strip()
        
        # Ensure times are 00:00 format
        for col in ['Start', 'End']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip().str.zfill(5)
        
        return data
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- 3. CURRENT TIME (US EASTERN) ---
tz = pytz.timezone('US/Eastern')
now = datetime.now(tz)
current_day = now.strftime("%A")
current_time = now.strftime("%H:%M")

# --- 12 HOUR HELPER FUNCTION ---
def to_12h(time_str):
    try:
        # converts '14:30' to '2:30 PM'
        return datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p").lstrip('0')
    except:
        return time_str

# --- 4. LOGIC FUNCTION ---
def check_status(name_to_check, full_df):
    today_blocks = full_df[(full_df['Name'] == name_to_check) & (full_df['Day'] == current_day)]
    for _, row in today_blocks.iterrows():
        if str(row['Start']) <= current_time <= str(row['End']):
            return {"status": "Busy", "activity": row['Activity'], "until": row['End']}
    return {"status": "Free"}

# --- 5. DASHBOARD ---
st.title("🤝 Group Schedule Tracker")
st.write(f"Current App Time: **{current_time}** ({current_day})")

if not df.empty:
    # Get unique names and filter out any weird 'nan' values
    friends = sorted([str(n) for n in df['Name'].unique() if str(n).lower() != 'nan'])
    
    # Sidebar
    user_name = st.sidebar.selectbox("Select Your Name", friends)
    st.sidebar.subheader(f"Your {current_day} Schedule")
    my_sched = df[(df['Name'] == user_name) & (df['Day'] == current_day)].sort_values('Start')
    for _, r in my_sched.iterrows():
        start_12 = to_12h(r['Start'])
        end_12 = to_12h(r['End'])
        st.sidebar.write(f"🕒 {start_12} - {end_12}: {r['Activity']}")

    # Main columns
    free_list, busy_list = [], []
    for name in friends:
        info = check_status(name, df)
        
        if info['status'] == "Busy":
            display_until = to_12h(info['until'])
            busy_list.append(f"🔴 **{name}**: {info['activity']} (until {info['until']})")
        else:
            future = df[(df['Name'] == name) & (df['Day'] == current_day) & (df['Start'] > current_time)]
            if not future.empty:
                next_t = to_12h(future['Start'].min())
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
else:
    st.warning("Data is empty or headers are wrong. Please check your Google Sheet.")

st.button("Manual Refresh", on_click=st.cache_data.clear)
