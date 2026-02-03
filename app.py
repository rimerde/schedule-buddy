import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
# Ensure this link ends in output=csv
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQXqcR0QBwiJO_nTN9lf5PR9vP7Ps2Smuz8djDjo7s22or7-B_yoWy79NnEaJ1LWMkG2Elnc1mh1n0k/pub?output=csv"

st.set_page_config(page_title="Friend Tracker", layout="wide")

# --- 2. TIMEZONE & FORMATTING HELPERS ---
def get_current_time():
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    return now.strftime("%A"), now.strftime("%H:%M")

def to_12h(time_str):
    """Converts '14:30' to '2:30 PM'"""
    try:
        # %I is 12h hour, %M is minutes, %p is AM/PM
        return datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p").lstrip('0')
    except:
        return time_str

current_day, current_time = get_current_time()

# --- 3. LOAD DATA (ROBUST VERSION) ---
@st.cache_data(ttl=60) 
def load_data():
    try:
        data = pd.read_csv(SHEET_URL, on_bad_lines='skip', engine='python')
        
        # Clean headers (removes hidden spaces)
        data.columns = data.columns.str.strip()
        
        # Safety check for the 'Name' column
        if 'Name' not in data.columns:
            st.error(f"⚠️ 'Name' column not found! I see: {list(data.columns)}")
            return pd.DataFrame()

        # Drop truly empty rows and clean names
        data = data.dropna(subset=['Name'])
        data['Name'] = data['Name'].astype(str).str.strip()
        
        # Standardize time columns for comparison logic (09:00, 14:30)
        for col in ['Start', 'End']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip().str.zfill(5)
        
        return data
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- 4. STATUS LOGIC ---
def check_status(name_to_check, full_df):
    today_blocks = full_df[(full_df['Name'] == name_to_check) & (full_df['Day'] == current_day)]
    
    for _, row in today_blocks.iterrows():
        # Logical comparison happens in 24h format
        if str(row['Start']) <= current_time <= str(row['End']):
            return {
                "status": "Busy", 
                "activity": row['Activity'], 
                "until": row['End'],
                "location": row.get('Location', 'N/A')
            }
    return {"status": "Free"}

# --- 5. MAIN DASHBOARD ---
st.title("🤝 Group Schedule Tracker")
st.write(f"Current Time: **{to_12h(current_time)}** ({current_day})")

if not df.empty:
    # Get unique list of friends, ignoring empty/NaN entries
    friends = sorted([str(n) for n in df['Name'].unique() if str(n).lower() != 'nan'])
    
    # --- SIDEBAR: PERSONAL VIEW ---
    user_name = st.sidebar.selectbox("Select Your Name", friends)
    st.sidebar.subheader(f"Your {current_day} Schedule")
    
    my_sched = df[(df['Name'] == user_name) & (df['Day'] == current_day)].sort_values('Start')
    
    if not my_sched.empty:
        for _, r in my_sched.iterrows():
            # Displaying in 12h format
            st.sidebar.info(f"**{to_12h(r['Start'])} - {to_12h(r['End'])}**\n\n{r['Activity']}")
    else:
        st.sidebar.write("No classes today! 🌴")

    # --- MAIN COLUMNS: GROUP VIEW ---
    free_list = []
    busy_list = []

    for name in friends:
        info = check_status(name, df)
        
        if info['status'] == "Busy":
            busy_list.append(f"🔴 **{name}**: {info['activity']} (until {to_12h(info['until'])})")
        else:
            # Find next upcoming block
            future = df[(df['Name'] == name) & (df['Day'] == current_day) & (df['Start'] > current_time)]
            if not future.empty:
                next_start = future['Start'].min()
                free_list.append(f"🟢 **{name}**: Free until {to_12h(next_start)}")
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
    st.warning("Please check your Google Sheet connection and column headers.")

# Refresh button
if st.button("Manual Refresh"):
    st.cache_data.clear()
    st.rerun()
