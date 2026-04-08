#!/usr/bin/env python
# coding: utf-8

# In[1]:


import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.set_page_config(page_title="GPS Validation Pickup", layout="wide")

st.title("📍 GPS Validation Pickup System")


def split_longlat(val):
    try:
        val = str(val).replace(" ", "")
        lat, lon = val.split(',')
        lat, lon = float(lat), float(lon)

        # deteksi kebalik
        if abs(lat) > 90 and abs(lon) <= 90:
            lat, lon = lon, lat

        # validasi range
        if abs(lat) > 90 or abs(lon) > 180:
            return None, None

        return lat, lon
    except:
        return None, None


def valid_coord(lat, lon):
    if pd.isna(lat) or pd.isna(lon):
        return False
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return False
    return True


def hitung_jarak(row):
    try:
        lat1 = row['PICKUP STATUS LATITUDE']
        lon1 = row['PICKUP STATUS LONGITUDE']
        lat2 = row['VALIDASI_LAT']
        lon2 = row['VALIDASI_LON']

        if not valid_coord(lat1, lon1):
            return None
        if not valid_coord(lat2, lon2):
            return None

        point1 = (lat1, lon1)
        point2 = (lat2, lon2)

        return geodesic(point1, point2).meters
    except:
        return None


def zoning(jarak):
    if pd.isna(jarak):
        return None
    elif jarak <= 300:
        return "ZONE 1 (<=300m)"
    elif jarak <= 1000:
        return "ZONE 2 (300m - 1km)"
    elif jarak <= 5000:
        return "ZONE 3 (1km - 5km)"
    else:
        return "ZONE 4 (>5km)"



uploaded_file = st.file_uploader("📂 Upload File Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

   
    df.columns = df.columns.str.strip().str.upper()

    # konversi numeric
    df['PICKUP STATUS LATITUDE'] = pd.to_numeric(df['PICKUP STATUS LATITUDE'], errors='coerce')
    df['PICKUP STATUS LONGITUDE'] = pd.to_numeric(df['PICKUP STATUS LONGITUDE'], errors='coerce')

  
    df[['VALIDASI_LAT', 'VALIDASI_LON']] = df['LONGLAT VALIDASI'].apply(
        lambda x: pd.Series(split_longlat(x))
    )


    df['DISTANCE_METER'] = df.apply(hitung_jarak, axis=1)


    df['STATUS_VALIDASI'] = df['DISTANCE_METER'].apply(
        lambda x: True if pd.notna(x) and x <= 300 else False
    )


    df['ZONE'] = df['DISTANCE_METER'].apply(zoning)


    total = len(df)
    valid = df['STATUS_VALIDASI'].sum()
    avg_dist = df['DISTANCE_METER'].mean()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Data", total)
    col2.metric("Valid (<=300m)", valid)
    col3.metric("Rata-rata Jarak (m)", round(avg_dist, 2) if pd.notna(avg_dist) else 0)

    st.divider()


    zone_filter = st.selectbox(
        "Filter Zone",
        ["ALL", "ZONE 1 (<=300m)", "ZONE 2 (300m - 1km)", "ZONE 3 (1km - 5km)", "ZONE 4 (>5km)"]
    )

    if zone_filter != "ALL":
        df = df[df['ZONE'] == zone_filter]

    
    st.dataframe(df, use_container_width=True)

  
    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="⬇️ Download Hasil CSV",
        data=csv,
        file_name="hasil_validasi.csv",
        mime="text/csv"
    )

else:
    st.info("Silakan upload file Excel terlebih dahulu")


# ----

# ----
