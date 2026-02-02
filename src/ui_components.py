import streamlit as st

def metric_card(title, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="card-title">{title}</div>
            <div class="card-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# src/ui_components.py

def style_leaderboard(df):
    def _apply_podium_colors(row):
        gold = 'background-color: rgba(255, 215, 0, 0.2)'
        silver = 'background-color: rgba(192, 192, 192, 0.2)'
        bronze = 'background-color: rgba(205, 127, 50, 0.2)'
        
        if row['rank'] == 1: return [gold] * len(row)
        if row['rank'] == 2: return [silver] * len(row)
        if row['rank'] == 3: return [bronze] * len(row)
        return [''] * len(row)

    # 1. Start the styler
    styler = df.style
    
    # 2. Fix the decimal places (precision=0 for whole numbers)
    styler = styler.format(precision=0)
    
    # 3. Apply the colors and optional alignment
    return styler.apply(_apply_podium_colors, axis=1).set_properties(**{'text-align': 'center'})

# src/ui_components.py

def style_user_deep_dive(df):
    """
    Styles the deep dive table based on league position.
    1: Gold, 2-5: Light Blue, 18-20: Light Red.
    """
    def _apply_position_colors(row):
        gold = 'background-color: rgba(255, 215, 0, 0.2)'    # Position 1
        purple = 'background-color: rgba(187, 173, 230, 0.2)'  # Position 2-5
        red = 'background-color: rgba(255, 99, 71, 0.2)'     # Position 18-20
        
        pos = row['position']
        
        if pos == 1:
            return [gold] * len(row)
        elif 2 <= pos <= 5:
            return [purple] * len(row)
        elif 18 <= pos <= 20:
            return [red] * len(row)
        return [''] * len(row)

    return df.style.apply(_apply_position_colors, axis=1).format(precision=0)

def style_user_deep_dive_alt(df):
    """
    Styles the deep dive table based on how 'right' the prediction was.
    Uses proximity_score or difference logic.
    """
    def _apply_accuracy_colors(row):
        # HEX Codes with 0.3 transparency
        perfect_green = 'background-color: #00BB7799' # Perfect (0 diff)
        great_green   = 'background-color: #00BB7765' # Very Close (1 diff)
        good_green    = 'background-color: #00BB7735' # Close (1-2 diff)
        warning_gold  = 'background-color: #00BB7715' # Average (3-4 diff)
        light_red    = 'background-color: #FF000015' # Poor (5 diff)
        bad_red       = 'background-color: #FF000035' # Way off (>5 diff)
        
        # Calculate the absolute gap
        gap = abs(row['predicted_difference'])
        
        if gap == 0:
            return [perfect_green] * len(row)
        elif gap == 1:
            return [great_green] * len(row)
        elif gap <= 2:
            return [good_green] * len(row)
        elif gap <= 5:
            return [warning_gold] * len(row)
        elif gap <= 8:
            return [light_red] * len(row)
        else:
            return [bad_red] * len(row)

    return df.style.apply(_apply_accuracy_colors, axis=1).format({
    'predicted_difference': '{:+d}' # Forces + or - to show
}, precision=0)