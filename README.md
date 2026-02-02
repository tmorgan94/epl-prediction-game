# EPL Prediction Leaderboard

An interactive Streamlit dashboard that tracks and ranks player performance in Premier League predictions. This project uses data from the official FPL API and applies a custom scoring system to reward accuracy and bold predictions.

## Features
* **Live Standings:** Fetches real-time Premier League data to compare against user predictions.
* **Custom Scoring:** A tiered points system rewarding proximity to actual results.
* **Boldness Bonus:** Uses Z-Score analysis to identify "Brave" picks, awarding double points for high-risk, high-reward accuracy.
* **Dynamic Leaderboard:** Automatically ranks users based on their total accumulated score.

## Scoring Logic

The system uses a **10-point ceiling** with a **step of 2** for each position missed, plus a **5-point bonus** for perfect accuracy.

| Distance from Actual | Calculation | Points Awarded |
| :--- | :--- | :--- |
| **0 (Perfect Match)** | 10 (Ceiling) + 5 (Bonus) | **15** |
| **1 Place Off** | 10 - 2 | **8** | 
| **2 Places Off** | 10 - 4 | **6** | 
| **3 Places Off** | 10 - 6 | **4** | 
| **4 Places Off** | 10 - 8 | **2** | 
| **5+ Places Off** | 10 - 10 | **0** |

**Brave Prediction Multiplier:** If a user makes a prediction that deviates significantly from the average (Z-Score ≥ 1.5) and is accurate within 1 place, their points for that team are **doubled**.

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/epl-prediction-leaderboard.git
   cd epl-prediction-leaderboard
   ```

2. **Create and activate virtual environment:**
    ```bash
   python -m venv venv
    # Windows
    .\venv\Scripts\Activate.ps1
    # Mac/Linux
    source venv/bin/activate
    ```
3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4. **Run the app:**
    ```bash
    streamlit run streamlit_app.py
    ```