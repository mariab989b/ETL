import streamlit as st
from snowflake.snowpark.context import get_active_session
from datetime import datetime
import altair as alt

# Session Snowflake
session = get_active_session()

st.set_page_config(page_title="Data Quality Monitor", layout="wide", initial_sidebar_state="collapsed")


st.markdown("""
<style>
    /* Theme sombre */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Titres */
    h1, h2, h3 {
        color: #FAFAFA;
        font-weight: 600;
    }
    
    h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Métriques */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #FAFAFA;
        font-weight: 600;
    }
    
    [data-testid="stMetricLabel"] {
        color: #B3B3B3;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }
    
    /* Cards/Containers */
    div[data-testid="stHorizontalBlock"] {
        background-color: #1A1D24;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #2D3139;
    }
    
    /* Tableaux */
    .stDataFrame {
        background-color: #1A1D24;
        border: 1px solid #2D3139;
        border-radius: 8px;
    }
    
    table {
        background-color: #1A1D24 !important;
        color: #FAFAFA !important;
    }
    
    thead tr th {
        background-color: #262B35 !important;
        color: #FAFAFA !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #3D4350 !important;
    }
    
    tbody tr:hover {
        background-color: #262B35 !important;
    }
    
    /* Graphiques */
    [data-testid="stArrowVegaLiteChart"] {
        background-color: #1A1D24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3139;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #B3B3B3;
        background-color: transparent;
        border-bottom: 2px solid transparent;
        padding-bottom: 0.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        color: #4ECDC4;
        border-bottom-color: #4ECDC4;
    }
    
    /* Alert boxes */
    .stAlert {
        background-color: #1A1D24;
        border: 1px solid #2D3139;
        color: #FAFAFA;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1A1D24;
        color: #FAFAFA;
        border: 1px solid #2D3139;
        border-radius: 8px;
    }
    
    .streamlit-expanderContent {
        background-color: #1A1D24;
        border: 1px solid #2D3139;
    }
</style>
""", unsafe_allow_html=True)

# tiitre
st.title("Data Quality Monitor")
st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


alt.themes.register('dark_theme', lambda: {
    'config': {
        'background': '#1A1D24',
        'view': {'strokeWidth': 0},
        'axis': {
            'labelColor': '#B3B3B3',
            'titleColor': '#FAFAFA',
            'gridColor': '#2D3139',
            'domainColor': '#3D4350',
            'tickColor': '#3D4350'
        },
        'legend': {
            'labelColor': '#B3B3B3',
            'titleColor': '#FAFAFA'
        },
        'title': {
            'color': '#FAFAFA'
        }
    }
})
alt.themes.enable('dark_theme')

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Vue d'ensemble", "Complétude", "Cohérence", "Tendances"])


with tab1:
    
    counts_sql = """
    SELECT 
      (SELECT COUNT(*) FROM SALES_DATA.SALES_DATA.clients) AS nb_clients,
      (SELECT COUNT(*) FROM SALES_DATA.SALES_DATA.products) AS nb_products,
      (SELECT COUNT(*) FROM SALES_DATA.SALES_DATA.product_variants) AS nb_variants,
      (SELECT COUNT(*) FROM SALES_DATA.SALES_DATA.orders) AS nb_orders,
      (SELECT COUNT(*) FROM SALES_DATA.SALES_DATA.order_lines) AS nb_order_lines,
      (SELECT COUNT(*) FROM SALES_DATA.SALES_DATA.reviews) AS nb_reviews
    """
    counts = session.sql(counts_sql).collect()[0]
    
    st.subheader("Volume des données")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Clients", f"{counts['NB_CLIENTS']:,}")
    col2.metric("Produits", f"{counts['NB_PRODUCTS']:,}")
    col3.metric("Variants", f"{counts['NB_VARIANTS']:,}")
    col4.metric("Commandes", f"{counts['NB_ORDERS']:,}")
    col5.metric("Lignes", f"{counts['NB_ORDER_LINES']:,}")
    col6.metric("Avis", f"{counts['NB_REVIEWS']:,}")
    
    st.markdown("---")
    
    
    st.subheader("Score de qualité global")
    
    quality_checks = []
    
    
    email_check = session.sql("""
        SELECT 
          COUNT(*) AS total,
          SUM(CASE WHEN email LIKE '%@%' THEN 1 ELSE 0 END) AS valid_email
        FROM SALES_DATA.SALES_DATA.clients
    """).collect()[0]
    email_pct = 100 * email_check['VALID_EMAIL'] / email_check['TOTAL'] if email_check['TOTAL'] > 0 else 0
    quality_checks.append(('Emails valides', email_pct))
    
    
    orders_check = session.sql("""
        SELECT 
          COUNT(DISTINCT o.order_id) AS total_orders,
          COUNT(DISTINCT ol.order_id) AS orders_with_lines
        FROM SALES_DATA.SALES_DATA.orders o
        LEFT JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
    """).collect()[0]
    orders_pct = 100 * orders_check['ORDERS_WITH_LINES'] / orders_check['TOTAL_ORDERS'] if orders_check['TOTAL_ORDERS'] > 0 else 0
    quality_checks.append(('Commandes avec lignes', orders_pct))
    
    
    amounts_check = session.sql("""
        SELECT 
          COUNT(*) AS total,
          SUM(CASE WHEN total_ttc = total_ht + total_vat THEN 1 ELSE 0 END) AS correct_amounts
        FROM SALES_DATA.SALES_DATA.orders
    """).collect()[0]
    amounts_pct = 100 * amounts_check['CORRECT_AMOUNTS'] / amounts_check['TOTAL'] if amounts_check['TOTAL'] > 0 else 0
    quality_checks.append(('Cohérence montants', amounts_pct))
    
    
    active_check = session.sql("""
        SELECT 
          COUNT(*) AS total,
          SUM(CASE WHEN active = TRUE THEN 1 ELSE 0 END) AS active_variants
        FROM SALES_DATA.SALES_DATA.product_variants
    """).collect()[0]
    active_pct = 100 * active_check['ACTIVE_VARIANTS'] / active_check['TOTAL'] if active_check['TOTAL'] > 0 else 0
    quality_checks.append(('Variants actifs', active_pct))
    
    
    global_score = sum([score for _, score in quality_checks]) / len(quality_checks)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        
        if global_score >= 90:
            color = "#4ECDC4"
            status = "Excellent"
        elif global_score >= 75:
            color = "#FFD93D"
            status = "Bon"
        else:
            color = "#FF6B6B"
            status = "À améliorer"
        
        st.metric("Score global", f"{global_score:.1f}%", status)
        
        for check_name, check_score in quality_checks:
            if check_score >= 90:
                indicator = "●"
                ind_color = "#4ECDC4"
            elif check_score >= 75:
                indicator = "●"
                ind_color = "#FFD93D"
            else:
                indicator = "●"
                ind_color = "#FF6B6B"
        st.markdown(f"<div style='margin:0.5rem 0'><span style='color:{ind_color};font-size:1.2rem'>{indicator}</span> <span style='color:#B3B3B3'>{check_name}: {check_score:.1f}%</span></div>", unsafe_allow_html=True)
    
    with col2:
        import pandas as pd
        df_checks = pd.DataFrame(quality_checks, columns=['Check', 'Score'])
        
        
        df_checks['Color'] = df_checks['Score'].apply(
            lambda x: '#4ECDC4' if x >= 90 else ('#FFD93D' if x >= 75 else '#FF6B6B')
        )
        
        bars = alt.Chart(df_checks).mark_bar().encode(
            x=alt.X('Score:Q', title='Score (%)', scale=alt.Scale(domain=[0, 100])),
            y=alt.Y('Check:N', title='', sort='-x'),
            color=alt.Color('Color:N', scale=None, legend=None),
            tooltip=['Check:N', alt.Tooltip('Score:Q', format='.1f')]
        ).properties(height=200)
        
        st.altair_chart(bars, use_container_width=True)


with tab2:
    st.subheader("Analyse de complétude des champs")
    
    
    st.markdown("**Table CLIENTS**")
    client_completeness = session.sql("""
        SELECT 
          COUNT(*) AS total,
          SUM(CASE WHEN name IS NOT NULL THEN 1 ELSE 0 END) AS name_filled,
          SUM(CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END) AS email_filled,
          SUM(CASE WHEN phone IS NOT NULL THEN 1 ELSE 0 END) AS phone_filled,
          SUM(CASE WHEN street_address IS NOT NULL THEN 1 ELSE 0 END) AS address_filled,
          SUM(CASE WHEN city IS NOT NULL THEN 1 ELSE 0 END) AS city_filled,
          SUM(CASE WHEN postalcode IS NOT NULL THEN 1 ELSE 0 END) AS postal_filled,
          SUM(CASE WHEN date_of_birth IS NOT NULL THEN 1 ELSE 0 END) AS dob_filled
        FROM SALES_DATA.SALES_DATA.clients
    """).collect()[0]
    
    total_clients = client_completeness['TOTAL']
    client_fields = {
        'Nom': 100 * client_completeness['NAME_FILLED'] / total_clients,
        'Email': 100 * client_completeness['EMAIL_FILLED'] / total_clients,
        'Téléphone': 100 * client_completeness['PHONE_FILLED'] / total_clients,
        'Adresse': 100 * client_completeness['ADDRESS_FILLED'] / total_clients,
        'Ville': 100 * client_completeness['CITY_FILLED'] / total_clients,
        'Code postal': 100 * client_completeness['POSTAL_FILLED'] / total_clients,
        'Date naissance': 100 * client_completeness['DOB_FILLED'] / total_clients
    }
    
    import pandas as pd
    df_client_comp = pd.DataFrame(list(client_fields.items()), columns=['Field', 'Completeness'])
    df_client_comp['Color'] = df_client_comp['Completeness'].apply(
        lambda x: '#4ECDC4' if x >= 95 else ('#FFD93D' if x >= 80 else '#FF6B6B')
    )
    
    chart_client = alt.Chart(df_client_comp).mark_bar().encode(
        x=alt.X('Completeness:Q', title='Complétude (%)', scale=alt.Scale(domain=[0, 100])),
        y=alt.Y('Field:N', title='', sort='-x'),
        color=alt.Color('Color:N', scale=None, legend=None),
        tooltip=['Field:N', alt.Tooltip('Completeness:Q', format='.1f')]
    ).properties(height=250)
    
    st.altair_chart(chart_client, use_container_width=True)
    
    st.markdown("---")
    
    # Produit
    st.markdown("#### Table PRODUCTS & VARIANTS")
    product_completeness = session.sql("""
        SELECT 
          COUNT(*) AS total,
          SUM(CASE WHEN name IS NOT NULL THEN 1 ELSE 0 END) AS name_filled,
          SUM(CASE WHEN category IS NOT NULL THEN 1 ELSE 0 END) AS category_filled,
          SUM(CASE WHEN sub_category IS NOT NULL THEN 1 ELSE 0 END) AS subcat_filled,
          SUM(CASE WHEN gender IS NOT NULL THEN 1 ELSE 0 END) AS gender_filled
        FROM SALES_DATA.SALES_DATA.products
    """).collect()[0]
    
    total_products = product_completeness['TOTAL']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Nom", f"{100 * product_completeness['NAME_FILLED'] / total_products:.1f}%")
    col2.metric("Catégorie", f"{100 * product_completeness['CATEGORY_FILLED'] / total_products:.1f}%")
    col3.metric("Sous-catégorie", f"{100 * product_completeness['SUBCAT_FILLED'] / total_products:.1f}%")
    col4.metric("Genre", f"{100 * product_completeness['GENDER_FILLED'] / total_products:.1f}%")


with tab3:
    st.subheader("Contrôles de cohérence")
    st.markdown("**Cohérence des montants**")
    amount_issues = session.sql("""
        SELECT 
          order_id,
          total_ht,
          total_vat,
          total_ttc,
          (total_ht + total_vat) AS calculated_ttc,
          ABS(total_ttc - (total_ht + total_vat)) AS diff
        FROM SALES_DATA.SALES_DATA.orders
        WHERE ABS(total_ttc - (total_ht + total_vat)) > 0.01
        LIMIT 20
    """).to_pandas()
    
    if not amount_issues.empty:
        st.warning(f"⚠ {len(amount_issues)} commandes avec incohérence de montants détectées")
        with st.expander("Voir les détails"):
            st.dataframe(amount_issues, use_container_width=True, hide_index=True)
    else:
        st.success("✓ Tous les montants sont cohérents")
    
    st.markdown("---")
    
    
    st.markdown("**Cohérence des dates**")
    date_issues = session.sql("""
        SELECT 
          order_id,
          purchase_time,
          delivery_date,
          expiration_date,
          DATEDIFF(day, purchase_time::date, delivery_date) AS days_to_delivery
        FROM SALES_DATA.SALES_DATA.orders
        WHERE delivery_date <= purchase_time::date
           OR expiration_date < delivery_date
        LIMIT 20
    """).to_pandas()
    
    if not date_issues.empty:
        st.warning(f"⚠ {len(date_issues)} commandes avec incohérence de dates")
        with st.expander("Voir les détails"):
            st.dataframe(date_issues, use_container_width=True, hide_index=True)
    else:
        st.success("✓ Toutes les dates sont cohérentes")
    
    st.markdown("---")
    
    
    st.markdown("**Format des emails**")
    invalid_emails = session.sql("""
        SELECT 
          client_id,
          name,
          email
        FROM SALES_DATA.SALES_DATA.clients
        WHERE email NOT LIKE '%@%'
           OR email NOT LIKE '%.%'
        LIMIT 20
    """).to_pandas()
    
    if not invalid_emails.empty:
        st.warning(f"⚠ {len(invalid_emails)} emails invalides détectés")
        with st.expander("Voir les détails"):
            st.dataframe(invalid_emails, use_container_width=True, hide_index=True)
    else:
        st.success("✓ Tous les emails sont valides")
    
    st.markdown("---")
    
    
    st.markdown("**Détection de doublons**")
    duplicate_emails = session.sql("""
        SELECT 
          email,
          COUNT(*) AS nb_clients
        FROM SALES_DATA.SALES_DATA.clients
        GROUP BY 1
        HAVING COUNT(*) > 1
        ORDER BY 2 DESC
        LIMIT 20
    """).to_pandas()
    
    if not duplicate_emails.empty:
        st.warning(f"⚠ {len(duplicate_emails)} emails en doublon")
        with st.expander("Voir les détails"):
            st.dataframe(duplicate_emails, use_container_width=True, hide_index=True)
    else:
        st.success("✓ Aucun email en doublon")


with tab4:
    st.subheader("Évolution de la qualité des données")
    
    
    orders_trend = session.sql("""
        SELECT 
          purchase_time::date AS date,
          COUNT(*) AS nb_orders
        FROM SALES_DATA.SALES_DATA.orders
        WHERE purchase_time >= DATEADD(day, -30, CURRENT_DATE())
        GROUP BY 1
        ORDER BY 1
    """).to_pandas()
    
    if not orders_trend.empty:
        st.markdown("**Commandes (30 derniers jours)**")
        line_chart = alt.Chart(orders_trend).mark_line(point=True, strokeWidth=2).encode(
            x=alt.X('DATE:T', title=''),
            y=alt.Y('NB_ORDERS:Q', title='Nombre de commandes'),
            color=alt.value('#4ECDC4'),
            tooltip=[
                alt.Tooltip('DATE:T', title='Date'),
                alt.Tooltip('NB_ORDERS:Q', title='Commandes')
            ]
        ).properties(height=300)
        
        st.altair_chart(line_chart, use_container_width=True)
    
    st.markdown("---")
    
    
    clients_trend = session.sql("""
        SELECT 
          created_at::date AS date,
          COUNT(*) AS nb_new_clients
        FROM SALES_DATA.SALES_DATA.clients
        WHERE created_at >= DATEADD(day, -30, CURRENT_DATE())
        GROUP BY 1
        ORDER BY 1
    """).to_pandas()
    
    if not clients_trend.empty:
        st.markdown("**Nouveaux clients (30 derniers jours)**")
        area_chart = alt.Chart(clients_trend).mark_area(
            line={'color': '#FFD93D'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#FFD93D', offset=0),
                       alt.GradientStop(color='#1A1D24', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('DATE:T', title=''),
            y=alt.Y('NB_NEW_CLIENTS:Q', title='Nouveaux clients'),
            tooltip=[
                alt.Tooltip('DATE:T', title='Date'),
                alt.Tooltip('NB_NEW_CLIENTS:Q', title='Nouveaux clients')
            ]
        ).properties(height=300)
        
        st.altair_chart(area_chart, use_container_width=True)