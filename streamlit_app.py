import streamlit as st
import pandas as pd
import os

# Import custom modules
from src.data_loader import fetch_fpl_data
from src.data_transform import get_league_history, calculate_leaderboard
from src.plotting import plot_leaderboard_bar, plot_crowd_error, plot_rank_history
from src.ui_components import metric_card, style_leaderboard, style_user_deep_dive, style_user_deep_dive_alt

# 1. PAGE CONFIG
st.set_page_config(
    page_title="PL Predictions 2026",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. LOAD ASSETS (CSS)
css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. DATA PROCESSING
# st.cache_data so the app doesn't re-run the math on every click
@st.cache_data(ttl=86400)  # cache for 24 hours
def get_processed_data():
    df_predictions, df_teams, df_fixtures = fetch_fpl_data()
    df_league = get_league_history(df_fixtures=df_fixtures,df_teams=df_teams)
    df_leaderboard, df_merged = calculate_leaderboard(df_league, df_predictions)
    return df_leaderboard, df_merged

df_leaderboard, df_merged = get_processed_data()

# 4. SIDEBAR
st.sidebar.header("Filters")
gameweeks = sorted(df_leaderboard['gameweek'].dropna().unique().astype(int), reverse=True)
selected_gw = st.sidebar.selectbox("Select Gameweek", options=gameweeks, index=0)

# Filter data based on selection
df_current_lb = df_leaderboard[df_leaderboard['gameweek'] == selected_gw]

# 5. HEADER & METRIC CARDS
st.title('PL Predictions 2026')
st.subheader(f"Gameweek {int(selected_gw)}")

# Logic for Gainer/Loser
leader_name = df_current_lb.iloc[0]['name']

# Get the actual min and max movement values
max_move = df_current_lb['rank_movement'].max()
min_move = df_current_lb['rank_movement'].min()

# Identify Riser: Only show a name if someone actually moved up
if max_move > 0:
    biggest_gainer = df_current_lb.sort_values("rank_movement", ascending=False).iloc[0]['name']
    riser_value = f"↑ {int(max_move)}"
else:
    biggest_gainer = "No Change"
    riser_value = "No Change"

# Identify Faller: Only show a name if someone actually moved down
if min_move < 0:
    biggest_loser = df_current_lb.sort_values("rank_movement", ascending=True).iloc[0]['name']
    faller_value = f"↓ {int(abs(min_move))}"
else:
    biggest_loser = "No Change"
    faller_value = "No Change"

col1, col2, col3 = st.columns(3)
with col1:
    metric_card("🏆 Leader", leader_name)
with col2:
    metric_card("🔥 Biggest Riser", biggest_gainer)
with col3:
    metric_card("💀 Biggest Faller", biggest_loser)

# 6. VISUALIZATIONS
st.divider()
st.subheader('Points')
st.plotly_chart(plot_leaderboard_bar(df_current_lb, selected_gw), use_container_width=True)

# 7. LEADERBOARD TABLE
display_df = df_current_lb[['rank', 'name', 'proximity_score', 'perfect_match_score', 'boldness_score', 'total_score']]
styled_lb = style_leaderboard(display_df)

# 2. Display with your existing column_config
st.dataframe(
    styled_lb, 
    column_config={
        'rank': st.column_config.Column(label='', width='small'), 
        'name': 'Name',
        'proximity_score': 'Proximity Score',
        'perfect_match_score': 'Perfect Match Score',
        'boldness_score': 'Boldness Score',
        'total_score': 'Total'
    },
    hide_index=True,
    use_container_width=True
)

# 8. USER DEEP DIVE
st.divider()
st.header("Player Deep Dive")

# Selection Box
selected_user = st.selectbox("Pick a player:", df_current_lb['name'].unique())

# Prepare and style the data
user_data = df_merged[(df_merged['name'] == selected_user) & (df_merged['gameweek'] == selected_gw)]
display_df = user_data[['position', 'team', 'predicted_position', 'predicted_difference', 'proximity_score', 'perfect_match_score', 'boldness_score', 'total_score']].sort_values('position', ascending=True)

# Apply the new style
from src.ui_components import style_user_deep_dive
#styled_user_deep_dive = style_user_deep_dive(display_df)
styled_user_deep_dive_alt = style_user_deep_dive_alt(display_df)    

st.dataframe(
    #styled_user_deep_dive,
    styled_user_deep_dive_alt,
    column_config={
        'position': st.column_config.Column(label='', width='small'),
        'team': 'Team',
        'predicted_position': 'Predicted',
        'predicted_difference': 'Difference',
        'proximity_score': 'Proximity Score',
        'perfect_match_score': 'Perfect Match Score',
        'boldness_score': 'Boldness Score',
        'total_score': 'Total'
    },
    use_container_width=True,
    hide_index=True,
    height=750
)

# 3. Chart 
st.subheader("Rank History")
with st.container(): 
    plot_rank_history(df_leaderboard, selected_user, selected_gw=selected_gw,key=f"trend_{selected_user}")

# 9. META ANALYSIS

st.header("Meta Analysis")

# Calculate Mean Error per team

# 1. Filter for the specific gameweek first
df_gw_data = df_merged[df_merged['gameweek'] == selected_gw]

# 2. Calculate Mean Error per team for THIS gameweek
# mean_error = Actual Position - Average Predicted Position
team_errors = df_gw_data.groupby('team').agg({
    'position': 'first',             # Actual league position
    'predicted_position': 'mean'      # Average of all users
}).reset_index()

team_errors['mean_error'] = team_errors['position'] - team_errors['predicted_position']

# Identify the teams
most_overestimated = team_errors.sort_values("mean_error", ascending=False).iloc[0]['team']
most_underestimated = team_errors.sort_values("mean_error", ascending=True).iloc[0]['team']
most_predictable = team_errors.loc[team_errors['mean_error'].abs().idxmin()]['team']

# --- Team Highlights Row ---
col4, col5, col6 = st.columns(3)

with col4:
    metric_card("📉 Overestimated", most_overestimated)
with col5:
    metric_card("🚀 Underestimated", most_underestimated)
with col6:
    metric_card("🎯 Most Predictable", most_predictable)

st.divider()

st.plotly_chart(plot_crowd_error(df_merged, selected_gw), use_container_width=True)


