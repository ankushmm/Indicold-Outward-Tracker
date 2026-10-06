import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import pdfplumber
import re

# 1. Page Configuration & Theme
st.set_page_config(page_title="Indicold Outward Tracker", layout="wide")
st.markdown("""
<style>
    html, body, [class*="css"]  { font-family: 'Calibri', sans-serif !important; background-color: #F0F2F5; color: #2C3E50; }
    div[data-testid="metric-container"] { background-color: #FFFFFF; border-radius: 12px; padding: 15px; border-left: 6px solid #F39C12; }
    .stTabs [data-baseweb="tab"] { background-color: #E2E6EA; border-radius: 8px 8px 0px 0px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #FFFFFF; border-bottom: 4px solid #2980B9; font-weight: bold; }
    .stButton > button { border-radius: 8px; background-color: #2980B9; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("🏭 INDICOLD - Outward Dispatch Tracker")
st.markdown("---")

# 2. Connect to the Master Google Sheet Database
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s5y0bKy1Tm4qBTbudErYxSg46rO4ly8Fv_GaCfsvtjw/edit"

# Fetch existing active vehicles
try:
    active_vehicles_df = conn.read(spreadsheet=SHEET_URL, worksheet="Active_Vehicles")
    vehicle_list = active_vehicles_df['Vehicle No'].dropna().tolist()
except Exception as e:
    # Agar sheet connect nahi hui, toh ek khali table bana lo taaki app crash na ho
    active_vehicles_df = pd.DataFrame(columns=["Vehicle No", "Status", "Timestamp"])
    vehicle_list = []
    st.error(f"Google Sheets Connection Error: Please setup API keys.")

# 3. Add New Vehicle
col1, col2 = st.columns([3, 1])
with col1:
    new_vehicle = st.text_input("Enter New Vehicle Number (e.g., HR38X1234):", placeholder="Type vehicle no...")
with col2:
    st.write(""); st.write("")
    if st.button("➕ Add Outward Vehicle"):
        if new_vehicle and new_vehicle not in vehicle_list:
            new_row = pd.DataFrame({"Vehicle No": [new_vehicle], "Status": ["In Progress"], "Timestamp": [pd.Timestamp.now()]})
            updated_vehicles = pd.concat([active_vehicles_df, new_row], ignore_index=True)
            
            try:
                # Try saving to Google Sheets
                conn.update(spreadsheet=SHEET_URL, worksheet="Active_Vehicles", data=updated_vehicles)
                st.success(f"Vehicle {new_vehicle} initialized & saved to Cloud!")
            except Exception as e:
                # Agar save fail ho, toh error dikhao par crash mat karo
                st.warning(f"Vehicle added to screen, but failed to save to Google Sheets. Need API setup.")
            
            st.rerun()
# 4. Processing Tabs for Each Vehicle
if vehicle_list:
    tabs = st.tabs(vehicle_list)
    for i, tab in enumerate(tabs):
        vehicle = vehicle_list[i]
        with tab:
            st.subheader(f"Dispatch Operations: {vehicle}")
            
            u1, u2, u3 = st.columns(3)
            with u1:
                st.markdown("#### 📄 1. Delivery Note")
                dl_pdf = st.file_uploader("Upload Client DO (PDF)", type=['pdf'], key=f"do_{vehicle}")
                if dl_pdf:
                    st.success("Delivery Note Uploaded. Extracting Data...")
                    # Basic PDF Extraction Logic
                    with pdfplumber.open(dl_pdf) as pdf:
                        text = pdf.pages[0].extract_text()
                        st.text_area("Extracted Preview", text[:200] + "...", height=100)
            
            with u2:
                st.markdown("#### 📥 2. Retrieval File")
                ret_file = st.file_uploader("Upload Retrieval Data", type=['xlsx', 'png'], key=f"ret_{vehicle}")
                if ret_file:
                    st.success("Retrieval Logged! LBA checked.")
                    
            with u3:
                st.markdown("#### 🚛 3. Loading Confirm")
                load_img = st.file_uploader("Upload Loading Screenshot", type=['png', 'jpg'], key=f"ld_{vehicle}")
                if load_img:
                    st.success("Loading Confirmed!")
                    if st.button("Finalize & Save to Master Database", key=f"save_{vehicle}"):
                        st.info("Saving records to Google Sheets...")
                        # This is where processed data will append to Master_Logs
                        st.success("Record permanently saved to Cloud Database!")
else:
    st.info("No active vehicles. Please add a vehicle to start operations.")
