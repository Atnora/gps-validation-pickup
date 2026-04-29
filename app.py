#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="GPS Validation Pickup", layout="wide")

st.title("📍 GPS Validation Pickup Dashboard")


# =========================
# FUNCTIONS
# =========================

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
    return (-90 <= lat <= 90 and -180 <= lon <= 180)


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

        return geodesic((lat1, lon1), (lat2, lon2)).meters
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


# =========================
# UPLOAD FILE
# =========================

uploaded_file = st.file_uploader("📂 Upload File Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip().str.upper()

    # konversi numeric
    df['PICKUP STATUS LATITUDE'] = pd.to_numeric(df['PICKUP STATUS LATITUDE'], errors='coerce')
    df['PICKUP STATUS LONGITUDE'] = pd.to_numeric(df['PICKUP STATUS LONGITUDE'], errors='coerce')

    # split longlat validasi
    df[['VALIDASI_LAT', 'VALIDASI_LON']] = df['LONGLAT VALIDASI'].apply(
        lambda x: pd.Series(split_longlat(x))
    )

    # hitung jarak
    df['DISTANCE_METER'] = df.apply(hitung_jarak, axis=1)
    df['DISTANCE_KM'] = (df['DISTANCE_METER'] / 1000).round(2)

    # =========================
    # INTERACTIVE FILTER
    # =========================

    threshold = st.slider("🎯 Batas Validasi (meter)", 100, 1000, 300)

    df['STATUS_VALIDASI'] = df['DISTANCE_METER'].apply(
        lambda x: True if pd.notna(x) and x <= threshold else False
    )

    df['ZONE'] = df['DISTANCE_METER'].apply(zoning)

    # filter zone
    zone_filter = st.selectbox(
        "Filter Zone",
        ["ALL", "ZONE 1 (<=300m)", "ZONE 2 (300m - 1km)", "ZONE 3 (1km - 5km)", "ZONE 4 (>5km)"]
    )

    # filter courier
    courier_filter = st.multiselect(
        "Filter Courier",
        options=df['PICKUP COURIER'].dropna().unique()
    )

    # apply filter
    if zone_filter != "ALL":
        df = df[df['ZONE'] == zone_filter]

    if courier_filter:
        df = df[df['PICKUP COURIER'].isin(courier_filter)]

    # =========================
    # KPI
    # =========================

    total = len(df)
    valid = df['STATUS_VALIDASI'].sum()
    invalid = total - valid
    avg_km = df['DISTANCE_KM'].mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Data", total)
    col2.metric("Valid", valid)
    col3.metric("Tidak Valid", invalid)
    col4.metric("Rata-rata Jarak (km)", round(avg_km, 2) if pd.notna(avg_km) else 0)

    st.divider()

    # =========================
    # PIE CHART
    # =========================

    st.subheader("📊 Distribusi Zona")

    zone_counts = df['ZONE'].value_counts()

    fig, ax = plt.subplots()
    ax.pie(zone_counts, labels=zone_counts.index, autopct='%1.1f%%')
    ax.set_title("Distribusi Zona Pickup")

    st.pyplot(fig)

    # =========================
    # MAP
    # =========================

    st.subheader("🗺️ Peta Lokasi Pickup")

    map_df = df[['PICKUP STATUS LATITUDE', 'PICKUP STATUS LONGITUDE']].dropna()
    map_df.columns = ['lat', 'lon']

    st.map(map_df)

    # =========================
    # DATA TABLE
    # =========================

    st.subheader("📋 Data Detail")

    df_display = df.drop(columns=['VALIDASI_LAT', 'VALIDASI_LON'], errors='ignore')
    st.dataframe(df_display, use_container_width=True)

    # =========================
    # DOWNLOAD
    # =========================

    csv = df_display.to_csv(index=False).encode('utf-8')
    tanggal = datetime.now().strftime("%Y-%m-%d")

    st.download_button(
        label="⬇️ Download Hasil CSV",
        data=csv,
        file_name=f"hasil_validasi_{tanggal}.csv",
        mime="text/csv"
    )

else:
    st.info("Silakan upload file Excel terlebih dahulu")
