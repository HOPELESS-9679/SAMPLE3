import streamlit as st
import pandas as pd
import folium
import json
from geopy.distance import geodesic
from folium.plugins import LocateControl
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Nursery Locator", layout="wide")
st.title("🌱 Live Nursery Locator – Tap a Nursery to Get Distance")

# Load nursery Excel file
df = pd.read_excel("NURSARY.xlsx")

required_cols = ['Name', 'Latitude', 'Longitude', 'Capacity', 'PlantsAvailable', 'Contact']
if not all(col in df.columns for col in required_cols):
    st.error("❌ Excel must include: " + ", ".join(required_cols))
    st.stop()

# Load Khariar GeoJSON boundary
with open("khariar_boundary.geojson", "r") as f:
    khariar_geojson = json.load(f)

# Get real user location from browser
st.subheader("📡 Detecting your location...")
user_loc = streamlit_js_eval(
    js_expressions="navigator.geolocation.getCurrentPosition((pos) => pos.coords)",
    key="get_user_location"
)

if user_loc and "latitude" in user_loc and "longitude" in user_loc:
    user_coords = (user_loc["latitude"], user_loc["longitude"])
    st.success(f"📍 Your location: {user_coords[0]:.4f}, {user_coords[1]:.4f}")
else:
    user_coords = (20.5600, 84.1400)  # Fallback (Khariar)
    st.warning("⚠️ Location access denied or failed. Using Khariar fallback location.")

# Create folium map
m = folium.Map(location=user_coords, zoom_start=10)
LocateControl(auto_start=True).add_to(m)

# Add Khariar boundary
folium.GeoJson(
    khariar_geojson,
    name="Khariar Division",
    style_function=lambda feature: {
        'fillColor': 'yellow',
        'color': 'black',
        'weight': 2,
        'fillOpacity': 0.1
    }
).add_to(m)

# Add user location
folium.Marker(
    location=user_coords,
    tooltip="Your Location",
    icon=folium.Icon(color="blue", icon="user")
).add_to(m)

# Add nursery markers with unique IDs
for idx, row in df.iterrows():
    popup = folium.Popup(f"ID: {idx}", parse_html=True)
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=popup,
        icon=folium.Icon(color="green", icon="leaf")
    ).add_to(m)

# Nearest nursery detection
df['Distance_km'] = df.apply(lambda row: geodesic(user_coords, (row['Latitude'], row['Longitude'])).km, axis=1)
nearest = df.loc[df['Distance_km'].idxmin()]

# Add nearest nursery marker
folium.Marker(
    location=[nearest['Latitude'], nearest['Longitude']],
    popup=folium.Popup(f"<b>Nearest Nursery:</b><br>{nearest['Name']}<br>{nearest['Distance_km']:.2f} km away", max_width=300),
    icon=folium.Icon(color="red", icon="star")
).add_to(m)

# Show map and capture user clicks
st.subheader("🗺️ Click on a nursery marker to view details and distance from you")
map_data = st_folium(m, width=1000, height=600)

# If user clicked a marker
if map_data and map_data.get("last_object_clicked_tooltip"):
    # Get coordinates of clicked marker
    clicked_coords = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
    
    # Find closest nursery to clicked point
    df['ClickDistance'] = df.apply(lambda row: geodesic(clicked_coords, (row['Latitude'], row['Longitude'])).meters, axis=1)
    selected = df.loc[df['ClickDistance'].idxmin()]
    distance_from_user = geodesic(user_coords, (selected['Latitude'], selected['Longitude'])).km

    st.success(f"✅ Selected Nursery: {selected['Name']}")
    st.markdown(f"""
    **Distance from You:** {distance_from_user:.2f} km  
    **Capacity:** {selected['Capacity']}  
    **Plants Available:** {selected['PlantsAvailable']}  
    **Contact:** {selected['Contact']}  
    """)

# Show nearest nursery by default
else:
    st.subheader("📍 Nearest Nursery")
    st.markdown(f"""
    **Name:** {nearest['Name']}  
    **Distance:** {nearest['Distance_km']:.2f} km  
    **Capacity:** {nearest['Capacity']}  
    **Plants Available:** {nearest['PlantsAvailable']}  
    **Contact:** {nearest['Contact']}  
    """)
