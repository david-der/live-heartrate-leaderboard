import streamlit as st
import requests
import time
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timezone
import numpy as np

# Page config
st.set_page_config(
    page_title="Live Heart Rate Monitor",
    page_icon="❤️",
    layout="wide"
)

# Initialize session state and constants
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None
if 'hr_data' not in st.session_state:
    # Initialize with explicit dtypes to ensure consistency
    st.session_state.hr_data = pd.DataFrame({
        'timestamp': pd.Series(dtype='datetime64[ns, UTC]'),
        'heart_rate': pd.Series(dtype='float64'),
        'hr_zone': pd.Series(dtype='int64'),
        'estimated_power': pd.Series(dtype='float64'),
        'cumulative_calories_burned': pd.Series(dtype='float64')
    })

# Constants
LEADERBOARD_TIME_WINDOW = 300  # 5 minutes in seconds

# Function to update the live graph
def update_live_graph():
    try:
        if st.session_state.selected_user:
            response = requests.get(
                f"http://localhost:4000/consumption/getUserLiveHeartRateStats?user_name={st.session_state.selected_user}&window_seconds=60"
            )
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Convert data to DataFrame
                    new_data = pd.DataFrame([{
                        'timestamp': datetime.fromisoformat(d['processed_timestamp'].replace('Z', '+00:00')),
                        'heart_rate': d['heart_rate'],
                        'hr_zone': d['hr_zone'],
                        'estimated_power': d['estimated_power'],
                        'cumulative_calories_burned': d['cumulative_calories_burned']
                    } for d in data])
                    
                    # Update session state data
                    if st.session_state.hr_data.empty:
                        st.session_state.hr_data = new_data
                    else:
                        st.session_state.hr_data = pd.concat([st.session_state.hr_data, new_data], ignore_index=True)
                    
                    # Drop duplicates and sort by timestamp
                    st.session_state.hr_data = st.session_state.hr_data.drop_duplicates(subset=['timestamp'])
                    st.session_state.hr_data = st.session_state.hr_data.sort_values('timestamp')
                    
                    # Keep only last 60 seconds of data
                    cutoff_time = datetime.now(timezone.utc) - pd.Timedelta(seconds=60)
                    st.session_state.hr_data = st.session_state.hr_data[st.session_state.hr_data['timestamp'] > cutoff_time]
                    
                    # Return the most recent data point
                    return st.session_state.hr_data.iloc[-1] if not st.session_state.hr_data.empty else None
    except Exception as e:
        st.error(f"Failed to update graph: {str(e)}")
    return None

# Function to update the leaderboard
def update_leaderboard():
    try:
        response = requests.get(f"http://localhost:4000/consumption/getLeaderboard?time_window_seconds={LEADERBOARD_TIME_WINDOW}&limit=10")
        if response.status_code == 200:
            data = response.json()["entries"]
            df = pd.DataFrame(data)
            
            # Display only relevant columns
            display_cols = ['rank', 'user_name', 'avg_heart_rate', 'avg_power', 'total_calories']
            df_display = df[display_cols].copy()
            
            # Add styling to highlight selected user
            def highlight_selected_user(row):
                if row['user_name'] == st.session_state.selected_user:
                    return ['background-color: #FF4B4B30'] * len(row)
                return [''] * len(row)
            
            styled_df = df_display.style.apply(highlight_selected_user, axis=1)
            return styled_df
    except Exception as e:
        st.error(f"Failed to update leaderboard: {str(e)}")
    return None

# Title and user selection in the same row
title_col, select_col = st.columns([1, 1])
with title_col:
    st.title("❤️ Live Heart Rate Monitor")
with select_col:
    try:
        response = requests.get(f"http://localhost:4000/consumption/getLeaderboard?time_window_seconds={LEADERBOARD_TIME_WINDOW}&limit=100")
        if response.status_code == 200:
            users = [entry["user_name"] for entry in response.json()["entries"]]
            # Add some vertical space to align with title
            st.write("")
            selected_user = st.selectbox("Select User", users, label_visibility="collapsed")
            if selected_user != st.session_state.selected_user:
                st.session_state.selected_user = selected_user
                st.session_state.hr_data = pd.DataFrame({
                    'timestamp': pd.Series(dtype='datetime64[ns, UTC]'),
                    'heart_rate': pd.Series(dtype='float64'),
                    'hr_zone': pd.Series(dtype='int64'),
                    'estimated_power': pd.Series(dtype='float64'),
                    'cumulative_calories_burned': pd.Series(dtype='float64')
                })
    except Exception as e:
        st.error(f"Failed to fetch users: {str(e)}")
        users = []

# Metrics row
metrics_cols = st.columns(4)

# Update data and metrics
latest_data = update_live_graph()

# Display metrics
if latest_data is not None:
    metrics_cols[0].metric(
        "Heart Rate", 
        f"{latest_data['heart_rate']} BPM",
        delta=None
    )
    metrics_cols[1].metric(
        "Zone", 
        f"Zone {latest_data['hr_zone']}",
        delta=None
    )
    metrics_cols[2].metric(
        "Power", 
        f"{latest_data['estimated_power']}W",
        delta=None
    )
    metrics_cols[3].metric(
        "Calories", 
        f"{latest_data['cumulative_calories_burned']:.1f} kcal",
        delta=None
    )

# Create and update graph
if not st.session_state.hr_data.empty:
    fig = go.Figure()
    
    # Add heart rate trace
    fig.add_trace(go.Scatter(
        x=st.session_state.hr_data['timestamp'],
        y=st.session_state.hr_data['heart_rate'],
        mode='lines+markers',
        name='Heart Rate',
        line=dict(color='#FF4B4B', width=2),
        fill='tozeroy'
    ))
    
    # Add zone lines
    zone_colors = ['rgba(255,255,255,0.3)'] * 4
    zone_labels = ['Zone 1-2', 'Zone 2-3', 'Zone 3-4', 'Zone 4-5']
    zone_values = [120, 140, 160, 180]
    
    for value, label, color in zip(zone_values, zone_labels, zone_colors):
        fig.add_hline(
            y=value,
            line_dash="dash",
            line_color=color,
            annotation_text=label,
            annotation_position="right"
        )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Heart Rate (BPM)",
        showlegend=False,
        height=400,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            range=[
                st.session_state.hr_data['timestamp'].min(),
                st.session_state.hr_data['timestamp'].max()
            ]
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            range=[
                max(0, st.session_state.hr_data['heart_rate'].min() - 10),
                st.session_state.hr_data['heart_rate'].max() + 10
            ]
        )
    )
    
    # Display the graph
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available yet. Please wait for data to appear.")

# Leaderboard Section
st.header("🏆 Leaderboard")

leaderboard_df = update_leaderboard()
if leaderboard_df is not None:
    # Calculate height based on number of rows (approximately 35px per row plus 35px for header)
    num_rows = len(leaderboard_df.data)
    table_height = (num_rows + 1) * 35
    st.dataframe(leaderboard_df, use_container_width=True, height=table_height)
else:
    st.info("Loading leaderboard data...")

# Update frequency
time.sleep(1)
st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    Built with Streamlit ❤️ | Monitoring heart rates in real-time
</div>
""", unsafe_allow_html=True)
