import pandas as pd

def validate_team_names(df_predictions, df_teams):
    """Checks if any names in the CSV don't match the official FPL names."""
    official_names = set(df_teams['name'].unique())
    prediction_names = set(df_predictions['team'].unique())
    
    mismatches = prediction_names - official_names
    if mismatches:
        print(f"Warning: teams in the CSV do not match the API: {mismatches}")
    return mismatches

def get_league_history(df_fixtures, df_teams):
    # filter for finished matches only
    df_finished_only = df_fixtures[df_fixtures['finished'] == True].copy()
    # find maximum date for every gameweek
    df_gw_dates = df_finished_only.groupby('event')['kickoff_time'].max().reset_index()
    df_gw_dates.columns = ['gameweek', 'gw_finish_date']

    print(f"{len(df_gw_dates)} completed Gameweeks. Max date: {df_gw_dates['gw_finish_date'].max()}")

    all_snapshots = []

    for _, row in df_gw_dates.iterrows():
        gw_num = row['gameweek']
        end_date = row['gw_finish_date']
        
        # filter for finished matches before the GW end date
        mask = (df_finished_only['kickoff_time'] <= end_date)
        df_step = df_finished_only[mask]
        
        # calculate points and goals for each team
        points_list = []
        for _, match in df_step.iterrows():
            # home
            h_pts = 3 if match['team_h_score'] > match['team_a_score'] else (1 if match['team_h_score'] == match['team_a_score'] else 0)
            points_list.append({'id': match['team_h'], 'points': h_pts, 'goals_scored': match['team_h_score'], 'goals_against': match['team_a_score']})
            # away
            a_pts = 3 if match['team_a_score'] > match['team_h_score'] else (1 if match['team_a_score'] == match['team_h_score'] else 0)
            points_list.append({'id': match['team_a'], 'points': a_pts, 'goals_scored': match['team_a_score'], 'goals_against': match['team_h_score']})
        
        # aggregate by team
        snap = pd.DataFrame(points_list).groupby('id').sum().reset_index()
        snap['gameweek'] = gw_num
        snap['date'] = end_date
        
        all_snapshots.append(snap)

    df_cumulative = pd.concat(all_snapshots, ignore_index=True)
    # calculate goal difference
    df_cumulative['goals_difference'] = df_cumulative['goals_scored'] - df_cumulative['goals_against']

    # merge with team names
    df_league = pd.merge(df_cumulative, df_teams, on='id').rename(columns={'name': 'team'})

    # rank within each gameweek
    df_league = df_league.sort_values(by=['gameweek', 'points', 'goals_difference', 'goals_scored'], ascending=[True, False, False, False])
    df_league['position'] = df_league.groupby('gameweek')['points'].rank(method='first', ascending=False).astype(int)
    df_league = df_league[['gameweek', 'date', 'position', 'team', 'points', 'goals_difference', 'goals_scored', 'goals_against']]

    print("Historical league table recreated")

    return df_league.sort_values(['gameweek', 'position'])

def calculate_leaderboard(df_league, df_predictions):
    # Merge actual positions with predicted positions: row per gameweek, team, user
    df_merged = pd.merge(
        df_league[['gameweek', 'team', 'position']], 
        df_predictions, 
        on='team'
    )
    # Scoring Parameters
    PROXIMITY_MAX = 10 # Max points for proximity score
    PROXIMITY_STEP = 2 # Points decrease per position away
    PERFECT_MATCH_BONUS = 5 # Bonus for exact position
    BOLD_THRESHOLD = 1.5 # Z-Score required for a bold choice
    BOLD_ERROR = 0 # Max distance from actual to qualify for multiplier
    BOLD_BONUS = 5.0 # Bonus points for a bold choice

    # 1. Proximity Score calculation
    df_merged['predicted_difference'] = df_merged['position'] - df_merged['predicted_position']
    # Calculate proximity and floor to 0 (no negative scores)
    df_merged['proximity_score'] = (PROXIMITY_MAX - (df_merged['predicted_difference'].abs() * PROXIMITY_STEP)).clip(lower=0)

    # 2. Perfect Match Bonus
    df_merged['perfect_match_score'] = 0
    mask_perfect = df_merged['position'] == df_merged['predicted_position']
    df_merged.loc[mask_perfect, 'perfect_match_score'] = PERFECT_MATCH_BONUS

    # 3. Statistical Boldness using z-score
    df_stats = df_predictions.groupby('team')['predicted_position'].agg(['mean', 'std']).reset_index()
    df_stats['std'] = df_stats['std'].replace(0, 1.0)
    df_stats.columns = ['team', 'crowd_mean', 'crowd_std']
    
    df_merged = pd.merge(df_merged, df_stats, on='team')
    
    df_merged['z_score'] = (df_merged['predicted_position'] - df_merged['crowd_mean']).abs() / df_merged['crowd_std']

    # 4. Calculate THE BONUS COLUMN
    # Step A: Identify Bold Hits
    is_bold = df_merged['z_score'] >= BOLD_THRESHOLD
    is_accurate = df_merged['predicted_difference'].abs() <= BOLD_ERROR
    mask_bold_hit = is_bold & is_accurate
    
    df_merged['boldness_score'] = 0.0
    # Assign the flat bonus to rows that meet the criteria
    df_merged.loc[mask_bold_hit, 'boldness_score'] = BOLD_BONUS

    # 5. Total Score
    df_merged['total_score'] = (
        df_merged['proximity_score'] + 
        df_merged['perfect_match_score'] + 
        df_merged['boldness_score']
    )
    # Additional total score column without boldness
    df_merged['total_score_no_boldness'] = (
        df_merged['proximity_score'] + 
        df_merged['perfect_match_score']
    )

    # 6. Aggregate to User/Gameweek level
    df_leaderboard = df_merged.groupby(['gameweek', 'name']).agg({
        'proximity_score': 'sum',
        'perfect_match_score': 'sum',
        'boldness_score': 'sum',
        'total_score': 'sum',
        'total_score_no_boldness': 'sum'
    }).reset_index()

    # 7. Final Ranking
    df_leaderboard['rank'] = df_leaderboard.groupby('gameweek')['total_score'].rank(
        ascending=False, method='min'
    )
    df_leaderboard['rank_no_boldness'] = df_leaderboard.groupby('gameweek')['total_score_no_boldness'].rank(
        ascending=False, method='min'
    )

    # 8. Calculate Movements
    # Sort by name and gameweek to ensure shift() picks up the correct previous week
    df_leaderboard = df_leaderboard.sort_values(['name', 'gameweek'])
    
    # We group by 'name' so we don't accidentally compare Player A's GW2 to Player B's GW1
    group = df_leaderboard.groupby('name')

    # Rank Movement (Previous Rank - Current Rank) 
    # Positive means you moved "up" the leaderboard (e.g., from 5th to 2nd is +3)
    df_leaderboard['rank_movement'] = group['rank'].shift(1) - df_leaderboard['rank']
    df_leaderboard['rank_no_boldness_movement'] = group['rank_no_boldness'].shift(1) - df_leaderboard['rank_no_boldness']

    # Score Movement (Current Score - Previous Score)
    # Shows how many points you earned specifically in this gameweek
    df_leaderboard['total_score_movement'] = df_leaderboard['total_score'] - group['total_score'].shift(1)
    df_leaderboard['total_score_no_boldness_movement'] = df_leaderboard['total_score_no_boldness'] - group['total_score_no_boldness'].shift(1)

    # 9. Clean up NaN values
    # The first gameweek (GW1) will have NaN because there is no "previous" week. 
    # We fill these with 0.
    movement_cols = [
        'rank_movement', 'rank_no_boldness_movement', 
        'total_score_movement', 'total_score_no_boldness_movement'
    ]
    df_leaderboard[movement_cols] = df_leaderboard[movement_cols].fillna(0)

    # Resort by gameweek and rank for the final output
    df_leaderboard = df_leaderboard.sort_values(['gameweek', 'rank'], ascending=[False, True])
    
    df_leaderboard = df_leaderboard.sort_values(['gameweek', 'total_score'], ascending=[True, False])
    
    print("Leaderboard calculated")

    return df_leaderboard, df_merged