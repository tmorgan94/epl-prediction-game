import plotly.express as px
import plotly.graph_objects as go
import streamlit_echarts as st_echarts

# src/plotting.py

def plot_leaderboard_bar(df_current_lb, selected_gw):
    fig = px.bar(
        df_current_lb, 
        x='name', 
        y='total_score',
        text='total_score',  # 1. Add the text labels
        title=' ',
        color='name', 
        color_discrete_sequence=[
            '#FFD700', '#C0C0C0', '#CD7F32', # Gold, Silver, Bronze
            '#F64271', '#F64271', '#F64271', '#F64271' # Red for others
        ]
    )
    
    fig.update_traces(
        textposition='outside', # 2. Position the points above the bars
        cliponaxis=False,       # Prevents numbers at the top from being cut off
        textfont_size=12,
        textfont_family='Arial'
    )
    
    fig.update_layout(
        xaxis_title=' ',
        yaxis_title='',
        font=dict(family='Arial', size=12),
        title_font=dict(family='Arial', size=16),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        
        # 3. Remove the Y-axis numbers and grid lines
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False
        ),
        
        # Add extra margin at the top so labels have room
        margin=dict(t=50) 
    )
    
    return fig

def plot_crowd_error(df_merged, selected_gw):
    meta_df = df_merged[df_merged['gameweek'] == selected_gw].groupby('team')['predicted_difference'].mean().reset_index()
    meta_df = meta_df.sort_values('predicted_difference', ascending=True)
    
    fig = px.bar(
        meta_df, 
        x='predicted_difference', 
        y='team', 
        orientation='h',
        color='predicted_difference', 
        color_continuous_scale='Reds',
        title="Average Error by Team (Lower is Better)"
    )
    fig.update_layout(
        xaxis_title='Average Predicted Difference',
        yaxis_title='Team',
        font=dict(family='Arial', size=12),
        title_font=dict(family='Arial', size=16),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        coloraxis_colorbar=dict(
            title="Error",
            tickvals=[meta_df['predicted_difference'].min(), meta_df['predicted_difference'].max()],
            ticktext=['Low Error', 'High Error']
        )
    )
    return fig

from streamlit_echarts import st_echarts

def plot_rank_history(df_leaderboard, user_name, selected_gw, key=None):
    user_df = df_leaderboard[
        (df_leaderboard['name'] == user_name) & 
        (df_leaderboard['gameweek'] <= selected_gw)
    ].sort_values('gameweek')
    
    x_data = user_df['gameweek'].tolist()
    y_data = user_df['rank'].tolist()

    options = {
        "animation": True,
        "xAxis": {"type": "category", "data": x_data, "name": ""},
        "yAxis": {
            "type": "value", 
            "inverse": True, 
            "min": 1, 
            "interval": 1,
            "name": "",
            "splitLine": {"show": False} # Clean up grid lines to show bands better
        },
        "series": [{
            "data": y_data,
            "type": "line",
            "smooth": True,
            "lineStyle": {"width": 4, "color": "#E90052"},
            "animationDuration": 3000,
            "animationEasing": "cubicInOut",
            # Add the horizontal bands here
            "markArea": {
                "silent": True, # Don't interfere with mouse tooltips
                "data": [
                    # Gold Band (Rank 1)
                    [
                        {"yAxis": 0.5, "itemStyle": {"color": "rgba(255, 215, 0, 0.15)"}}, 
                        {"yAxis": 1.5}
                    ],
                    # Silver Band (Rank 2)
                    [
                        {"yAxis": 1.5, "itemStyle": {"color": "rgba(192, 192, 192, 0.15)"}}, 
                        {"yAxis": 2.5}
                    ],
                    # Bronze Band (Rank 3)
                    [
                        {"yAxis": 2.5, "itemStyle": {"color": "rgba(205, 127, 50, 0.15)"}}, 
                        {"yAxis": 3.5}
                    ]
                ]
            }
        }]
    }
    
    return st_echarts(options=options, height="400px", key=key)

def plot_crowd_error(df_merged, selected_gw):
    # 1. Aggregate error for all players per team
    meta_df = df_merged[df_merged['gameweek'] == selected_gw].groupby('team').agg({
        'predicted_difference': 'mean'
    }).reset_index()
    
    # 2. Sort by difference to make the chart readable
    meta_df = meta_df.sort_values('predicted_difference', ascending=True)

    # 3. Create the bar chart
    fig = px.bar(
        meta_df,
        x='predicted_difference',
        y='team',
        title="Average Prediction Error by Team<br><sup>Red = Overestimated, Blue = Underestimated</sup>",
        orientation='h',
        text_auto='.1f', # Shows 1 decimal place on the bars
        color='predicted_difference',
        # Red-Blue scale: Red for positive (Hype), Blue for negative (Surprise)
        color_continuous_scale=['#1F77B4', '#D3D3D3', '#FF4B4B'], 
        color_continuous_midpoint=0
    )

    fig.update_layout(
        xaxis_title="Average Positions Off",
        yaxis_title="",
        showlegend=False,
        
        coloraxis_showscale=False, # Hide the color bar for a cleaner look
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    # Add a vertical line at 0 for the "Perfect Consensus" mark
    fig.add_vline(x=0, line_dash="solid", line_color="grey", opacity=0.2)

    return fig
