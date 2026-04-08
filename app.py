#!/usr/bin/env python
# coding: utf-8

# In[1]:


import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from datetime import datetime
import pydeck as pdk

st.set_page_config(page_title="GPS Validation Dashboard", layout="wide")

st.title("📍 GPS Validation Dashboard (PRO)")


def split_longlat(val):
    try:
        val = str(val).replace(" ", "")
        lat, lon = val.split(',')
        lat, lon = float(lat), float(lon)

        if abs(lat) > 90 and abs(lon) <= 90:
            lat, lon = lon, lat

        if abs(lat) > 90 or abs(lon) > 180:
            return None, None

        return lat, lon
    except:
        return None, None


def valid_coord(lat, lon):
    return pd.notna(lat) and pd.notna(lon) and (-90 <= lat <= 90 and -180 <= lon <= 180)


def hitung_jarak(row):
    try:
        lat1, lon1 = row['PICKUP STATUS LATITUDE'], row['PICKUP STATUS LONGITUDE']
        lat2, lon2 = row['VALIDASI_LAT'], row['VALIDASI_LON']

        if not valid_coord(lat1, lon1) or not valid_coord(lat2, lon2):
            return None

        return geodesic((lat1, lon1), (lat2, lon2)).meters
    except:
        return None


def zoning(jarak):
    if pd.isna(jarak):
        return "UNKNOWN"
    elif jarak <= 300:
        return "ZONE 1"
    elif jarak <= 1000:
        return "ZONE 2"
    elif jarak <= 5000:
        return "ZONE 3"
    else:
        return "ZONE 4"


def zone_color(zone):
    return {
        "ZONE 1": [0, 200, 0],
        "ZONE 2": [255, 200, 0],
        "ZONE 3": [255, 100, 0],
        "ZONE 4": [255, 0, 0],
        "UNKNOWN": [150, 150, 150]
    }.get(zone, [150, 150, 150])


uploaded_file = st.file_uploader("📂 Upload File Excel", type=["xlsx"])

if uploaded_file:

    @st.cache_data
    def process_data(file):
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip().str.upper()

        df['PICKUP STATUS LATITUDE'] = pd.to_numeric(df['PICKUP STATUS LATITUDE'], errors='coerce')
        df['PICKUP STATUS LONGITUDE'] = pd.to_numeric(df['PICKUP STATUS LONGITUDE'], errors='coerce')

        df[['VALIDASI_LAT', 'VALIDASI_LON']] = df['LONGLAT VALIDASI'].apply(
            lambda x: pd.Series(split_longlat(x))
        )

        df['DISTANCE_METER'] = df.apply(hitung_jarak, axis=1)
        df['ZONE'] = df['DISTANCE_METER'].apply(zoning)
        df['STATUS_VALIDASI'] = df['DISTANCE_METER'] <= 300

        return df

    df = process_data(uploaded_file)


    total = len(df)
    valid = df['STATUS_VALIDASI'].sum()
    avg = df['DISTANCE_METER'].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Data", total)
    col2.metric("Valid (≤300m)", valid)
    col3.metric("Avg Distance (m)", round(avg, 2) if pd.notna(avg) else 0)

    st.divider()

    zone_filter = st.multiselect(
        "Filter Zone",
        df['ZONE'].unique(),
        default=df['ZONE'].unique()
    )

    df = df[df['ZONE'].isin(zone_filter)]


    st.subheader("📊 Distribusi Zone")
    st.bar_chart(df['ZONE'].value_counts())


    st.subheader("🗺️ Map Visualisasi")

    df_map = df.dropna(subset=['PICKUP STATUS LATITUDE', 'PICKUP STATUS LONGITUDE']).copy()
    df_map["color"] = df_map["ZONE"].apply(zone_color)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position='[PICKUP STATUS LONGITUDE, PICKUP STATUS LATITUDE]',
        get_fill_color="color",
        get_radius=50,
    )

    view_state = pdk.ViewState(
        latitude=df_map['PICKUP STATUS LATITUDE'].mean(),
        longitude=df_map['PICKUP STATUS LONGITUDE'].mean(),
        zoom=10
    )

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

    st.subheader("📋 Data Detail")

    df_display = df.drop(columns=['VALIDASI_LAT', 'VALIDASI_LON'], errors='ignore')
    st.dataframe(df_display, use_container_width=True)


    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"hasil_validasi_{timestamp}.csv"

    csv = df_display.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="⬇️ Download Hasil",
        data=csv,
        file_name=file_name,
        mime="text/csv"
    )

else:
    st.info("Silakan upload file Excel")


# ----

# ----
