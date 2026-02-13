import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# ---------------------------------------------------
# Page config
# ---------------------------------------------------
st.set_page_config(page_title="Earthquake Analysis", layout="wide")

# ---------------------------------------------------
# MYSQL CONNECTION
# ---------------------------------------------------
host = "localhost"
port = 3306
database = "b115_b118"
username = "root"
password = quote_plus("12345")

# Create MySQL connection string
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}")

# ---------------------------------------------------
# CSS (unchanged)
# ---------------------------------------------------
st.markdown(
    """
    <style>
    .reportview-container .main .block-container{
        padding-top: 0.75rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100% !important;
    }
    .stDataFrame, .stTable {
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# UI
# ---------------------------------------------------
st.title("🌍 Earthquake Data Analysis Dashboard")
st.markdown("Select any problem statement to run the corresponding SQL query.")

# ---------------------------------------------------
# SQL QUERIES (MySQL syntax)
# ---------------------------------------------------
queries = {
        "1. Top 10 strongest earthquakes (mag)": """
        SELECT *
        FROM earthquakes_data
        ORDER BY mag DESC
        LIMIT 10
        """,

        "2. Top 10 deepest earthquakes (depth_km)": """
        SELECT *
        FROM earthquakes_data
        ORDER BY depth_km DESC
        LIMIT 10
        """,

        "3. Shallow earthquakes (<50 km) and mag > 7.5": """
        SELECT *
        FROM earthquakes_data
        WHERE depth_km < 50 AND mag > 7.5
        """,

        "4. Average depth per continent": """
        SELECT sources, AVG(depth_km) AS avg_depth
        FROM earthquakes_data
        GROUP BY sources
        """,

        "5. Average magnitude per magnitude type (magType)": """
        SELECT magType, AVG(mag) AS avg_magnitude
        FROM earthquakes_data
        GROUP BY magType
        """,

        # -------------------- Time Analysis --------------------
        "6. Year with most earthquakes": """
        SELECT YEAR(time) AS year, COUNT(*) AS total_earthquakes
        FROM earthquakes_data
        GROUP BY YEAR(time)
        ORDER BY total_earthquakes DESC
        """,

        "7. Month with highest number of earthquakes": """
        SELECT MONTH(time) AS month, COUNT(*) AS total_earthquakes
        FROM earthquakes_data
        GROUP BY MONTH(time)
        ORDER BY total_earthquakes DESC
        """,

        "8. Day of week with most earthquakes": """
        SELECT day_of_week, COUNT(*) AS total_earthquakes
        FROM earthquakes_data
        GROUP BY day_of_week
        ORDER BY total_earthquakes DESC;

        """,

        "9. Count of earthquakes per hour of day": """
        SELECT HOUR(time) AS hour_of_day,
        COUNT(*) AS total_earthquakes
        FROM earthquakes_data
        GROUP BY HOUR(time)
        ORDER BY hour_of_day;

        """,

        "10. Most active reporting network (net)": """
        SELECT net, COUNT(*) AS total_reports
        FROM earthquakes_data
        GROUP BY net
        ORDER BY total_reports DESC
        """,

        # -------------------- Casualties & Economic Loss --------------------
        "11. Top 5 places with highest casualties": """
        SELECT place,
        SUM(sig) AS total_significance
        FROM earthquakes_data
        GROUP BY place
        ORDER BY total_significance DESC
        limit 5;
        """,

        "12. Total estimated economic loss per continent": """
        SELECT 
            CASE 
                WHEN country IN ('India','China','Japan','Indonesia','Nepal','Pakistan') THEN 'Asia'
                WHEN country IN ('USA','Canada','Mexico') THEN 'North America'
                WHEN country IN ('Brazil','Chile','Peru','Argentina') THEN 'South America'
                WHEN country IN ('Germany','France','Italy','Turkey','Greece','UK','Spain') THEN 'Europe'
                WHEN country IN ('Australia','New Zealand') THEN 'Oceania'
                WHEN country IN ('Egypt','Morocco','South Africa','Nigeria') THEN 'Africa'
                ELSE 'Other'
            END AS continent,

            SUM(POWER(10, mag) * 100000) AS total_loss

        FROM earthquakes_data

        GROUP BY 
            CASE 
                WHEN country IN ('India','China','Japan','Indonesia','Nepal','Pakistan') THEN 'Asia'
                WHEN country IN ('USA','Canada','Mexico') THEN 'North America'
                WHEN country IN ('Brazil','Chile','Peru','Argentina') THEN 'South America'
                WHEN country IN ('Germany','France','Italy','Turkey','Greece','UK','Spain') THEN 'Europe'
                WHEN country IN ('Australia','New Zealand') THEN 'Oceania'
                WHEN country IN ('Egypt','Morocco','South Africa','Nigeria') THEN 'Africa'
                ELSE 'Other'
            END

        ORDER BY total_loss DESC;

        """,

        "13. Average economic loss by alert level": """
        SELECT 
            CASE 
                WHEN sig >= 1000 THEN 'Red'
                WHEN sig >= 500 THEN 'Orange'
                WHEN sig >= 200 THEN 'Yellow'
                ELSE 'Green'
            END AS alert,

            AVG(POWER(10, mag) * 100000) AS avg_loss

        FROM earthquakes_data

        GROUP BY 
            CASE 
                WHEN sig >= 1000 THEN 'Red'
                WHEN sig >= 500 THEN 'Orange'
                WHEN sig >= 200 THEN 'Yellow'
                ELSE 'Green'
            END

        ORDER BY avg_loss DESC;

        """,

        # -------------------- Event Type & Quality Metrics --------------------
        "14. Reviewed vs automatic earthquakes (status)": """
        SELECT status, COUNT(*) AS total_events
        FROM earthquakes_data
        GROUP BY status
        """,

        "15. Count by earthquake type (type)": """
        SELECT type, COUNT(*) AS total_events
        FROM earthquakes_data
        GROUP BY type
        """,

        "16. Number of earthquakes by data type (types)": """
        SELECT types, COUNT(*) AS total_events
        FROM earthquakes_data
        GROUP BY types
        """,

        "17. Average RMS and gap per continent": """
        SELECT 
            CASE 
                WHEN country IN ('India','China','Japan','Indonesia','Nepal','Pakistan') THEN 'Asia'
                WHEN country IN ('USA','Canada','Mexico') THEN 'North America'
                WHEN country IN ('Brazil','Chile','Peru','Argentina') THEN 'South America'
                WHEN country IN ('Germany','France','Italy','Turkey','Greece','UK','Spain') THEN 'Europe'
                WHEN country IN ('Australia','New Zealand') THEN 'Oceania'
                WHEN country IN ('Egypt','Morocco','South Africa','Nigeria') THEN 'Africa'
                ELSE 'Other'
            END AS continent,

            AVG(rms) AS avg_rms,
            AVG(gap) AS avg_gap

        FROM earthquakes_data

        GROUP BY 
            CASE 
                WHEN country IN ('India','China','Japan','Indonesia','Nepal','Pakistan') THEN 'Asia'
                WHEN country IN ('USA','Canada','Mexico') THEN 'North America'
                WHEN country IN ('Brazil','Chile','Peru','Argentina') THEN 'South America'
                WHEN country IN ('Germany','France','Italy','Turkey','Greece','UK','Spain') THEN 'Europe'
                WHEN country IN ('Australia','New Zealand') THEN 'Oceania'
                WHEN country IN ('Egypt','Morocco','South Africa','Nigeria') THEN 'Africa'
                ELSE 'Other'
            END

        ORDER BY continent;

        """,

        "18. Events with high station coverage (nst > 100)": """
        SELECT *
        FROM earthquakes_data
        WHERE nst > 100
        """,

        # -------------------- Tsunamis & Alerts --------------------
        "19. Number of tsunamis triggered per year": """
        SELECT YEAR(time) AS year, COUNT(*) AS tsunami_events
        FROM earthquakes_data
        WHERE tsunami = 1
        GROUP BY YEAR(time)
        ORDER BY year
        """,

        "20. Count earthquakes by alert levels": """
        SELECT 
            CASE 
                WHEN sig >= 1000 THEN 'Red'
                WHEN sig >= 500 THEN 'Orange'
                WHEN sig >= 200 THEN 'Yellow'
                ELSE 'Green'
            END AS alert,

            COUNT(*) AS total_events

        FROM earthquakes_data

        GROUP BY 
            CASE 
                WHEN sig >= 1000 THEN 'Red'
                WHEN sig >= 500 THEN 'Orange'
                WHEN sig >= 200 THEN 'Yellow'
                ELSE 'Green'
            END

        ORDER BY total_events DESC;

        """,

        # -------------------- Seismic Pattern & Trends --------------------
        "21. Top 5 countries by highest avg magnitude (last 10 years)": """
        SELECT 
            country,
            AVG(mag) AS avg_magnitude
        FROM earthquakes_data
        WHERE time >= DATE_SUB(CURDATE(), INTERVAL 10 YEAR)
        GROUP BY country
        ORDER BY avg_magnitude DESC
        LIMIT 5;

        """,

        "22. Countries with both shallow and deep earthquakes in same month": """
        SELECT 
            country,
            YEAR(time) AS year,
            MONTH(time) AS month
        FROM earthquakes_data
        GROUP BY 
            country,
            YEAR(time),
            MONTH(time)
        HAVING 
            MAX(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) = 1
            AND
            MAX(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) = 1;

        """,

        "23. Year-over-year growth rate of earthquakes": """
        WITH yearly AS (
            SELECT YEAR(time) AS year, COUNT(*) AS total_earthquakes
            FROM earthquakes_data
            GROUP BY YEAR(time)
        )
        SELECT y1.year,
            y1.total_earthquakes,
            ((y1.total_earthquakes - y2.total_earthquakes) * 100.0 /
                y2.total_earthquakes) AS yoy_growth_percent
        FROM yearly y1
        JOIN yearly y2 ON y1.year = y2.year + 1
        """,

        "24. Top 3 most seismically active regions": """
        SELECT place as Region,
            COUNT(*) AS frequency,
            AVG(mag) AS avg_magnitude,
            COUNT(*) * AVG(mag) AS activity_score
        FROM earthquakes_data
        GROUP BY Region 
        ORDER BY activity_score DESC
        LIMIT 3
        """,

        # -------------------- Depth, Location & Distance Analysis --------------------
        "25. Avg depth near equator (±5° latitude)": """
        SELECT 
            country,
            AVG(latitude) AS avg_latitude,
            AVG(depth_km) AS avg_depth
        FROM earthquakes_data
        WHERE latitude BETWEEN -5 AND 5
        AND depth_km IS NOT NULL
        GROUP BY country
        ORDER BY avg_depth DESC;


        """,

        "26. Countries with highest shallow-to-deep ratio": """
        SELECT 
            country,
            SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) /
            NULLIF(SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END), 0)
            AS shallow_deep_ratio
        FROM earthquakes_data
        GROUP BY country
        ORDER BY shallow_deep_ratio DESC;

        """,

        "27. Avg magnitude difference (tsunami vs non-tsunami)": """
        SELECT
            (SELECT AVG(mag) FROM earthquakes_data WHERE tsunami = 1) -
            (SELECT AVG(mag) FROM earthquakes_data WHERE tsunami = 0)
            AS avg_magnitude_difference
        """,

        "28. Lowest data reliability (highest rms + gap)": """
        SELECT *,
            (rms + gap) AS error_score
        FROM earthquakes_data
        WHERE rms IS NOT NULL
        AND gap IS NOT NULL
        ORDER BY error_score DESC
        LIMIT 10;

        """,

        "29. Consecutive earthquakes within 50 km and 1 hour": """
        WITH q AS (
        SELECT
            id, place, time, latitude, longitude,
            LAG(id) OVER (ORDER BY time) pid,
            LAG(place) OVER (ORDER BY time) pplace,
            LAG(time) OVER (ORDER BY time) pt,
            LAG(latitude) OVER (ORDER BY time) plat,
            LAG(longitude) OVER (ORDER BY time) plon
        FROM earthquakes_data
        )
        SELECT
        pid   AS eq1_id,
        pplace AS eq1_place,
        id    AS eq2_id,
        place AS eq2_place
        FROM q
        WHERE pid IS NOT NULL
        AND TIMESTAMPDIFF(MINUTE, pt, time) <= 60
        AND 6371 * ACOS(
                COS(RADIANS(plat)) * COS(RADIANS(latitude)) *
                COS(RADIANS(longitude) - RADIANS(plon)) +
                SIN(RADIANS(plat)) * SIN(RADIANS(latitude))
            ) <= 50;


        """,

        "30. Determine the regions with the highest frequency of deep-focus earthquakes (depth > 300 km).": """
        SELECT place, COUNT(*) AS total
        FROM earthquakes_data
        WHERE depth_km > 300
        GROUP BY place
        ORDER BY total DESC;

        """
}

# ---------------------------------------------------
# Dropdown + Button (unchanged layout)
# ---------------------------------------------------
col1, _ = st.columns([4, 1])
with col1:
    selected_task = st.selectbox(
        "Choose Task Number",
        options=list(queries.keys()),
        index=0
    )

    btn_left, btn_right = st.columns([1, 3])
    with btn_left:
        run_button = st.button("Run Query", use_container_width=True)

# ---------------------------------------------------
# RUN QUERY
# ---------------------------------------------------
if run_button:
    st.markdown(f"### Results for: {selected_task}")

    sql = queries[selected_task]

    try:
        result = pd.read_sql(sql, engine)
        st.dataframe(result, use_container_width=True, height=520)

    except Exception as e:
        st.error(f"❌ Error executing query: {e}")
