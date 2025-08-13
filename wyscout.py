import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle, ConnectionPatch

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Football Event Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Matplotlib Pitch Drawing Function ---
def draw_pitch(ax, pitch_color='#1e1e1e', line_color='#c7d5cc'):
    """
    Draws a football pitch on a matplotlib axes.
    """
    ax.set_facecolor(pitch_color)
    
    # Pitch Outline & Center Line
    ax.plot([0, 0], [0, 90], color=line_color)
    ax.plot([0, 130], [90, 90], color=line_color)
    ax.plot([130, 130], [90, 0], color=line_color)
    ax.plot([130, 0], [0, 0], color=line_color)
    ax.plot([65, 65], [0, 90], color=line_color)
    
    # Left Penalty Area
    ax.plot([16.5, 16.5], [65, 25], color=line_color)
    ax.plot([0, 16.5], [65, 65], color=line_color)
    ax.plot([16.5, 0], [25, 25], color=line_color)
    
    # Right Penalty Area
    ax.plot([130, 113.5], [65, 65], color=line_color)
    ax.plot([113.5, 113.5], [65, 25], color=line_color)
    ax.plot([113.5, 130], [25, 25], color=line_color)
    
    # Left 6-yard Box
    ax.plot([0, 5.5], [54, 54], color=line_color)
    ax.plot([5.5, 5.5], [54, 36], color=line_color)
    ax.plot([5.5, 0.5], [36, 36], color=line_color)
    
    # Right 6-yard Box
    ax.plot([130, 124.5], [54, 54], color=line_color)
    ax.plot([124.5, 124.5], [54, 36], color=line_color)
    ax.plot([124.5, 130], [36, 36], color=line_color)
    
    # Circles
    centreCircle = plt.Circle((65, 45), 9.15, color=line_color, fill=False)
    centreSpot = plt.Circle((65, 45), 0.8, color=line_color)
    leftPenSpot = plt.Circle((11, 45), 0.8, color=line_color)
    rightPenSpot = plt.Circle((119, 45), 0.8, color=line_color)
    ax.add_patch(centreCircle)
    ax.add_patch(centreSpot)
    ax.add_patch(leftPenSpot)
    ax.add_patch(rightPenSpot)
    
    # Arcs
    leftArc = Arc((11, 45), height=18.3, width=18.3, angle=0, theta1=310, theta2=50, color=line_color)
    rightArc = Arc((119, 45), height=18.3, width=18.3, angle=0, theta1=130, theta2=230, color=line_color)
    ax.add_patch(leftArc)
    ax.add_patch(rightArc)
    
    # Set limits and remove ticks
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 90)
    ax.set_xticks([])
    ax.set_yticks([])
    
    return ax

# --- 3. Data Loading and Processing ---
@st.cache_data
def load_data(uploaded_file):
    """
    Loads and processes the event data CSV.
    """
    if uploaded_file is None:
        return None
    try:
        df = pd.read_csv(uploaded_file)
        # Standardize column names for easier access
        df.columns = [
            'Timeline', 'StartTime', 'Duration', 'Row', 'InstanceNumber', 
            'StartThird', 'StartFlank', 'EndThird', 'EndFlank', 'Length', 
            'NumEvents', 'Outcome', 'Transition', 'xG', 'Players', 
            'StartX', 'StartY', 'EventDuration', 'Formation', 'EndX', 'EndY', 
            'Ungrouped', 'Notes', 'Flags'
        ]
        # Convert relevant columns to numeric
        for col in ['StartX', 'StartY', 'EndX', 'EndY', 'xG']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows where coordinates are missing
        df.dropna(subset=['StartX', 'StartY'], inplace=True)
        return df
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

# --- 4. Sidebar ---
with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Choose an event tag CSV file", type="csv")
    st.info("Upload the event data to generate match analysis.")

# --- 5. Main Dashboard ---
st.title("Match Event Analysis Dashboard")

if uploaded_file is None:
    st.warning("Please upload a CSV file to begin analysis.")
else:
    df = load_data(uploaded_file)
    
    if df is not None:
        # Extract match name from the 'Timeline' column
        match_name = df['Timeline'].iloc[0]
        st.header(f"Analysis for: {match_name}")
        
        # Filter for shots
        shots_df = df[df['Row'].str.contains("Shot", na=False)].copy()
        goals_df = shots_df[shots_df['Outcome'] == 'Shot on goal'] # Assuming 'Shot on goal' is a goal for this data

        # --- KPI Row ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Shots", len(shots_df))
        col2.metric("Goals Scored", len(goals_df))
        col3.metric("Total xG", f"{shots_df['xG'].sum():.2f}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # --- Shot Map ---
            st.subheader("Shot Map")
            fig, ax = plt.subplots(figsize=(10, 7))
            fig.set_facecolor('#1e1e1e')
            ax = draw_pitch(ax)
            
            # Plot shots
            for i, shot in shots_df.iterrows():
                x = shot['StartX'] * 1.3 # Scale X to fit 130-unit pitch
                y = shot['StartY'] * 0.9 # Scale Y to fit 90-unit pitch
                
                # Determine color by outcome
                color = 'red' if shot['Outcome'] == 'Shot on goal' else 'white'
                
                # Size by xG, with a minimum size
                size = shot['xG'] * 500 + 100 if pd.notna(shot['xG']) else 100
                
                ax.scatter(x, y, s=size, c=color, alpha=0.7, edgecolors='w')
                if shot['Outcome'] == 'Shot on goal':
                    ax.scatter(x, y, s=size*1.2, facecolors='none', edgecolors='red', lw=2)


            ax.set_title("Shot Locations and xG (size)", color='white', fontsize=14)
            st.pyplot(fig)

        with col2:
            # --- Action Heatmap ---
            st.subheader("Action Heatmap")
            fig_hm, ax_hm = plt.subplots(figsize=(10, 7))
            fig_hm.set_facecolor('#1e1e1e')
            ax_hm = draw_pitch(ax_hm)
            
            # Create the heatmap
            # Using a 2D histogram (hexbin) for a cleaner look
            x_coords = df['StartX'] * 1.3
            y_coords = df['StartY'] * 0.9
            
            ax_hm.hexbin(x_coords, y_coords, gridsize=20, cmap='inferno', alpha=0.7)
            ax_hm.set_title("All Player Actions Heatmap", color='white', fontsize=14)
            st.pyplot(fig_hm)
            
        st.divider()
        
        # --- Data Table ---
        st.subheader("Event Data")
        st.dataframe(df.head(20))
