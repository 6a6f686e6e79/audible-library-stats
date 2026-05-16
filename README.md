# Audible Library Stats

An interactive dashboard for exploring your personal Audible library. Authenticate once with the Audible API, fetch your full library data, and browse it through a Streamlit web app with charts, filters, and deep-dive views.

## What It Does

- **Authenticate** (`audible_auth.py`) — logs into Audible and saves a local auth token (run once)
- **Fetch data** (`audible_stats.py`) — pulls your full library, listening stats, finished books, and wishlist from the Audible API; prints a summary to the terminal and saves everything to `audible_data.json`
- **Explore** (`audible_app.py`) — a Streamlit dashboard with:
  - Top-level metrics: total books, hours listened, finished/in-progress/not-started counts
  - Filterable library table with CSV export
  - Charts: purchases by year, status breakdown, top authors, longest books, avg book length over time
  - Author deep dive with finish-rate stats
  - "Almost Finished" shelf (books at 90%+ progress)
  - Full-text book search

## Setup

**1. Clone the repo**
```bash
git clone <repo-url>
cd audible-library-stats
```

**2. Create and activate a virtual environment**
```bash
# Mac / Linux
python3 -m venv audible-env
source audible-env/bin/activate

# Windows
python -m venv audible-env
.\audible-env\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

## Usage

### Step 1 — Authenticate (one time only)
```bash
python audible_auth.py
```
Enter your Audible/Amazon email and password when prompted. This saves `audible_auth.json` locally — keep it private, it is excluded from git.

### Step 2 — Fetch your library data
```bash
python audible_stats.py
```
This pulls your library, listening stats, finished books, and wishlist from the Audible API and saves them to `audible_data.json`. It also prints a summary to the terminal (purchases by year, top authors, longest books, backlog hours). Re-run anytime to refresh your data.

### Step 3 — Launch the dashboard
```bash
streamlit run audible_app.py
```
Opens the interactive dashboard in your browser at `http://localhost:8501`.

## Files

| File | Purpose |
|------|---------|
| `audible_auth.py` | One-time authentication with the Audible API |
| `audible_stats.py` | Fetches library data and prints a terminal summary |
| `audible_app.py` | Streamlit dashboard |
| `requirements.txt` | Python dependencies |
| `audible_auth.json` | Auth token — **gitignored, never commit** |
| `audible_data.json` | Cached library data — **gitignored, never commit** |

## Privacy

`audible_auth.json` and `audible_data.json` are listed in `.gitignore` and will not be committed. Do not share these files — they contain your Audible credentials and personal library data.
