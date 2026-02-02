import requests
import pandas as pd
import os

def fetch_fpl_data(predictions_path='data/epl_predictions_2026.csv'):
    # predictions data from csv
    predictions_path = 'data/epl_predictions_2026.csv'
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Missing predictions file at {predictions_path}")
    df_predictions = pd.read_csv(predictions_path)
    
    # pull data from FPL API
    base_url = 'https://fantasy.premierleague.com/api/'
    try:
        bootstrap_data = requests.get(f'{base_url}bootstrap-static/', timeout=10).json()
        fixtures_data = requests.get(f'{base_url}fixtures/', timeout=10).json()
    except Exception as e:
        print(f"API Error: {e}")
        return None, None, df_predictions

    # Store as basic DataFrames
    df_teams = pd.DataFrame(bootstrap_data['teams'])[['id', 'name']]
    df_fixtures = pd.DataFrame(fixtures_data)
    df_fixtures['kickoff_time'] = pd.to_datetime(df_fixtures['kickoff_time']).dt.date

    print(f"Predictions data fetched: {len(df_predictions)} predictions")
    print(f"FPL API data fetched: {len(df_fixtures)} fixtures")

    return df_predictions, df_teams, df_fixtures