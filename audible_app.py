"""
audible_app.py
Interactive Audible Library Dashboard
Run with: streamlit run audible_app.py
"""

import streamlit as st
import pandas as pd
import json
import os

# ── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="Audible Library",
    page_icon="🎧",
    layout="wide"
)

# ── LOAD DATA ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open('audible_data.json', 'r') as f:
        raw = json.load(f)

    books = raw.get('library', [])
    rows = []
    for b in books:
        authors = b.get('authors') or []
        author_str = ', '.join([a.get('name', '') for a in authors if isinstance(a, dict)])
        ls = b.get('listening_status') or {}
        pd_raw = str(b.get('purchase_date', '') or '')[:10]
        finished_at = str(ls.get('finished_at_timestamp', '') or '')[:10]
        runtime_min = b.get('runtime_length_min', 0) or 0
        pct = b.get('percent_complete', 0) or 0
        is_finished = b.get('is_finished', False)

        if is_finished:
            status = 'Finished'
        elif pct > 0:
            status = 'In Progress'
        else:
            status = 'Not Started'

        rows.append({
            'Title': b.get('title', 'Unknown'),
            'Author': author_str,
            'Hours': round(runtime_min / 60, 1),
            'Progress %': pct,
            'Status': status,
            'Finished': is_finished,
            'Purchase Date': pd_raw,
            'Purchase Year': pd_raw[:4] if pd_raw else 'Unknown',
            'Finished At': finished_at,
            'ASIN': b.get('asin', ''),
        })

    df = pd.DataFrame(rows)
    total_ms = raw.get('total_stats', {}).get('aggregated_total_listening_stats', {}).get('aggregated_sum', 0)
    return df, total_ms

# ── CHECK FILE EXISTS ─────────────────────────────────────────
if not os.path.exists('audible_data.json'):
    st.error("audible_data.json not found. Run audible_stats.py first.")
    st.stop()

df, total_ms = load_data()
total_hours = round(total_ms / 3600000, 1)

# ── HEADER ────────────────────────────────────────────────────
st.title("🎧 Audible Library Dashboard")
st.caption("Interactive explorer — data from the Audible API")

# ── TOP METRICS ───────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Books", len(df))
col2.metric("Hours Listened", f"{total_hours:,}")
col3.metric("Finished", len(df[df['Status'] == 'Finished']))
col4.metric("In Progress", len(df[df['Status'] == 'In Progress']))
col5.metric("Not Started", len(df[df['Status'] == 'Not Started']))

st.divider()

# ── SIDEBAR FILTERS ───────────────────────────────────────────
st.sidebar.header("🔍 Filters")

search = st.sidebar.text_input("Search title or author", "")

all_authors = sorted(df['Author'].dropna().unique().tolist())
selected_authors = st.sidebar.multiselect("Filter by author", all_authors)

all_statuses = ['Finished', 'In Progress', 'Not Started']
selected_statuses = st.sidebar.multiselect("Filter by status", all_statuses, default=all_statuses)

all_years = sorted(df['Purchase Year'].unique().tolist())
selected_years = st.sidebar.multiselect("Filter by purchase year", all_years)

min_hours = float(df['Hours'].min())
max_hours = float(df['Hours'].max())
hour_range = st.sidebar.slider(
    "Book length (hours)",
    min_value=min_hours,
    max_value=max_hours,
    value=(min_hours, max_hours),
    step=0.5
)

# ── APPLY FILTERS ─────────────────────────────────────────────
filtered = df.copy()

if search:
    mask = (
        filtered['Title'].str.contains(search, case=False, na=False) |
        filtered['Author'].str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]

if selected_authors:
    filtered = filtered[filtered['Author'].isin(selected_authors)]

if selected_statuses:
    filtered = filtered[filtered['Status'].isin(selected_statuses)]

if selected_years:
    filtered = filtered[filtered['Purchase Year'].isin(selected_years)]

filtered = filtered[
    (filtered['Hours'] >= hour_range[0]) &
    (filtered['Hours'] <= hour_range[1])
]

st.caption(f"Showing {len(filtered)} of {len(df)} books")

# ── TABS ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📚 Library", "📊 Charts", "🔬 Deep Dive"])

# ── TAB 1: LIBRARY TABLE ──────────────────────────────────────
with tab1:
    sort_col = st.selectbox("Sort by", ['Title', 'Author', 'Hours', 'Progress %', 'Purchase Date', 'Status'], index=4)
    sort_asc = st.checkbox("Ascending", value=False)

    display = filtered[['Title', 'Author', 'Hours', 'Progress %', 'Status', 'Purchase Date', 'Finished At']].copy()
    display = display.sort_values(sort_col, ascending=sort_asc)

    st.dataframe(
        display,
        use_container_width=True,
        height=500,
        column_config={
            'Hours': st.column_config.NumberColumn(format="%.1f h"),
            'Progress %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
        }
    )

    csv = display.to_csv(index=False)
    st.download_button("⬇ Download filtered list as CSV", csv, "audible_filtered.csv", "text/csv")

# ── TAB 2: CHARTS ─────────────────────────────────────────────
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Purchases by Year")
        year_counts = filtered.groupby('Purchase Year').size().reset_index(name='Books')
        year_counts = year_counts[year_counts['Purchase Year'] != 'Unknown']
        st.bar_chart(year_counts.set_index('Purchase Year'))

    with col_b:
        st.subheader("Status Breakdown")
        status_counts = filtered['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        st.bar_chart(status_counts.set_index('Status'))

    st.subheader("Top Authors by Book Count")
    author_counts = (
        filtered['Author']
        .value_counts()
        .head(10)
        .reset_index()
    )
    author_counts.columns = ['Author', 'Books']
    st.bar_chart(author_counts.set_index('Author'))

    st.subheader("Top 10 Longest Books")
    longest = filtered.nlargest(10, 'Hours')[['Title', 'Author', 'Hours', 'Status']]
    st.dataframe(longest, use_container_width=True, hide_index=True)

    st.subheader("Average Book Length by Purchase Year")
    avg_len = (
        filtered[filtered['Purchase Year'] != 'Unknown']
        .groupby('Purchase Year')['Hours']
        .mean()
        .round(1)
        .reset_index()
    )
    avg_len.columns = ['Year', 'Avg Hours']
    st.line_chart(avg_len.set_index('Year'))

# ── TAB 3: DEEP DIVE ──────────────────────────────────────────
with tab3:
    st.subheader("Author Deep Dive")
    author_pick = st.selectbox("Select an author", all_authors)

    author_books = df[df['Author'] == author_pick].copy()
    author_books = author_books.sort_values('Purchase Date')

    finished_n = len(author_books[author_books['Status'] == 'Finished'])
    total_n = len(author_books)
    total_h = author_books['Hours'].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Books", total_n)
    m2.metric("Total Hours", f"{round(total_h, 1)}h")
    m3.metric("Finish Rate", f"{round(finished_n/total_n*100) if total_n else 0}%")

    st.dataframe(
        author_books[['Title', 'Hours', 'Progress %', 'Status', 'Purchase Date']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'Hours': st.column_config.NumberColumn(format="%.1f h"),
            'Progress %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
        }
    )

    st.divider()
    st.subheader("Almost Finished Shelf")
    st.caption("Books at 90%+ that aren't marked done")
    almost = df[(df['Progress %'] >= 90) & (~df['Finished'])].copy()
    almost = almost.sort_values('Progress %', ascending=False)
    st.dataframe(
        almost[['Title', 'Author', 'Hours', 'Progress %', 'Purchase Date']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'Progress %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
        }
    )

    st.divider()
    st.subheader("Spotlight: Search Any Book")
    book_search = st.text_input("Search for a specific book")
    if book_search:
        results = df[df['Title'].str.contains(book_search, case=False, na=False)]
        if len(results):
            for _, row in results.iterrows():
                st.write(f"**{row['Title']}** by {row['Author']}")
                st.write(f"- Runtime: {row['Hours']}h | Progress: {row['Progress %']}% | Status: {row['Status']}")
                st.write(f"- Purchased: {row['Purchase Date']} | Last finished: {row['Finished At'] or 'N/A'}")
                st.divider()
        else:
            st.info("No books found matching that search.")
