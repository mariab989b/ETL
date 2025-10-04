import streamlit as st
from snowflake.snowpark.context import get_active_session
from datetime import datetime, date
import altair as alt

# --- Session Snowflake (automatique dans Streamlit in Snowflake)
session = get_active_session()

st.set_page_config(page_title="Maison Albert - KPIs", layout="wide", initial_sidebar_state="expanded")

# Style CSS personnalisé inspiré de Maison Albert
st.markdown("""
<style>
    /* Palette beige/crème épurée */
    :root {
        --beige-clair: #F5F1E8;
        --beige-moyen: #E8DFD0;
        --beige-fonce: #C9B99B;
        --taupe: #8B7E74;
        --noir-doux: #2C2825;
    }
    
    /* Fond général */
    .stApp {
        background-color: #F5F1E8;
    }
    
    /* Titre principal */
    h1 {
        font-family: 'Didot', 'Bodoni MT', 'Playfair Display', serif;
        color: #2C2825;
        font-weight: 300;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        font-size: 2.5rem !important;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #C9B99B;
    }
    
    /* Sous-titres */
    h2, h3 {
        font-family: 'Didot', 'Bodoni MT', 'Playfair Display', serif;
        color: #2C2825;
        font-weight: 300;
        letter-spacing: 0.1em;
    }
    
    /* Cartes métriques */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #2C2825;
        font-weight: 300;
    }
    
    [data-testid="stMetricLabel"] {
        color: #8B7E74;
        font-size: 0.9rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #E8DFD0;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #2C2825;
        font-size: 1.2rem;
        letter-spacing: 0.1em;
    }
    
    /* Boutons et inputs */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #C9B99B;
        color: #2C2825;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #8B7E74;
        font-size: 0.9rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        border-bottom: 2px solid transparent;
        padding-bottom: 0.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        color: #2C2825;
        border-bottom-color: #C9B99B;
    }
    
    /* DataFrames */
    .stDataFrame {
        background-color: #FAF8F3;
        border: 1px solid #E8DFD0;
    }
    
    /* Tableaux */
    table {
        background-color: #FAF8F3 !important;
    }
    
    thead tr th {
        background-color: #E8DFD0 !important;
        color: #2C2825 !important;
        font-weight: 400 !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-size: 0.85rem !important;
        border-bottom: 2px solid #C9B99B !important;
    }
    
    tbody tr:hover {
        background-color: #F5F1E8 !important;
    }
    
    /* Graphiques */
    [data-testid="stArrowVegaLiteChart"] {
        background-color: #FAF8F3;
        padding: 1rem;
        border-radius: 4px;
        border: 1px solid #E8DFD0;
    }
    
    /* Personnalisation Vega-Lite pour les couleurs */
    .vega-embed {
        background-color: #FAF8F3 !important;
    }
    
    /* Séparateur */
    hr {
        border-color: #C9B99B;
        opacity: 0.3;
    }
    
    /* Info boxes */
    .stAlert {
        background-color: #E8DFD0;
        color: #2C2825;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# MAISON ALBERT")
st.markdown("### Tableau de bord")

# Configuration Altair pour la palette Maison Albert
alt.themes.register('maison_albert', lambda: {
    'config': {
        'view': {'strokeWidth': 0, 'continuousHeight': 350, 'continuousWidth': 400},
        'background': '#FAF8F3',
        'font': 'Didot, Bodoni MT, Playfair Display, serif',
        'axis': {
            'labelFontSize': 11,
            'labelColor': '#8B7E74',
            'titleFontSize': 12,
            'titleColor': '#2C2825',
            'gridColor': '#E8DFD0',
            'domainColor': '#C9B99B',
            'tickColor': '#C9B99B',
            'labelFontWeight': 300,
            'titleFontWeight': 400
        },
        'legend': {
            'labelFontSize': 11,
            'labelColor': '#8B7E74',
            'titleFontSize': 12,
            'titleColor': '#2C2825',
            'titleFontWeight': 400,
            'labelFontWeight': 300
        },
        'range': {
            'category': ['#C9B99B', '#8B7E74', '#E8DFD0', '#2C2825', '#F5F1E8'],
            'diverging': ['#2C2825', '#8B7E74', '#C9B99B', '#E8DFD0', '#F5F1E8']
        },
        'bar': {'fill': '#C9B99B'},
        'line': {'stroke': '#8B7E74', 'strokeWidth': 2},
        'point': {'fill': '#C9B99B'},
        'area': {'fill': '#E8DFD0'}
    }
})
alt.themes.enable('maison_albert')

# -----------------------------
# Filtres (barre latérale)
# -----------------------------
st.sidebar.header("Filtres")

# Bornes de dates dispo
dt_bounds_df = session.sql("""
    SELECT MIN(purchase_time) AS min_dt, MAX(purchase_time) AS max_dt
    FROM SALES_DATA.SALES_DATA.orders
""").collect()

# Si base vide, gérer proprement
if not dt_bounds_df or dt_bounds_df[0]["MIN_DT"] is None or dt_bounds_df[0]["MAX_DT"] is None:
    st.warning("Aucune commande trouvée dans SALES_DATA.SALES_DATA.orders.")
    st.stop()

min_dt = dt_bounds_df[0]["MIN_DT"]
max_dt = dt_bounds_df[0]["MAX_DT"]

# Convertir en date si ce sont des datetime
if isinstance(min_dt, datetime):
    min_dt = min_dt.date()
if isinstance(max_dt, datetime):
    max_dt = max_dt.date()

date_range = st.sidebar.date_input(
    "Période d'achat",
    value=(min_dt, max_dt),
    min_value=min_dt,
    max_value=max_dt
)

# Dimensions
cats_result = session.sql("""
    SELECT DISTINCT category FROM SALES_DATA.SALES_DATA.products 
    WHERE category IS NOT NULL
    ORDER BY 1
""").collect()
cats = [row["CATEGORY"] for row in cats_result]

sizes_result = session.sql("""
    SELECT DISTINCT size_label FROM SALES_DATA.SALES_DATA.product_variants 
    WHERE size_label IS NOT NULL
    ORDER BY 1
""").collect()
sizes = [row["SIZE_LABEL"] for row in sizes_result]

genders_result = session.sql("""
    SELECT DISTINCT gender FROM SALES_DATA.SALES_DATA.products 
    WHERE gender IS NOT NULL
    ORDER BY 1
""").collect()
genders = [row["GENDER"] for row in genders_result]

sel_cats = st.sidebar.multiselect("Catégorie olfactive", cats, default=(cats[:3] if len(cats) >= 3 else cats))
sel_sizes = st.sidebar.multiselect("Format", sizes, default=(sizes[:2] if len(sizes) >= 2 else sizes))
sel_genders = st.sidebar.multiselect("Genre produit", genders, default=genders)

# Construction sûre du WHERE commun
clauses = [f"o.purchase_time::date BETWEEN '{date_range[0]}' AND '{date_range[1]}'"]

if sel_cats:
    in_list = ",".join(["'" + c.replace("'", "''") + "'" for c in sel_cats])
    clauses.append(f"p.category IN ({in_list})")

if sel_sizes:
    in_list = ",".join(["'" + s.replace("'", "''") + "'" for s in sel_sizes])
    clauses.append(f"pv.size_label IN ({in_list})")

if sel_genders:
    in_list = ",".join(["'" + g.replace("'", "''") + "'" for g in sel_genders])
    clauses.append(f"p.gender IN ({in_list})")

WHERE = " AND ".join(clauses)

# -----------------------------
# Cartouche KPI (CA, commandes, panier, refunds)
# -----------------------------
kpi_sql = f"""
WITH f AS (
  SELECT o.order_id, o.total_ttc
  FROM SALES_DATA.SALES_DATA.orders o
  JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id=ol.order_id
  JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id=pv.product_variant_id
  JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id=p.product_id
  WHERE {WHERE}
),
refunds AS (
  SELECT DISTINCT order_id
  FROM SALES_DATA.SALES_DATA.order_status_history
  WHERE status='refunded'
)
SELECT
  COALESCE(SUM(f.total_ttc),0)                                     AS total_revenue,
  COUNT(DISTINCT f.order_id)                                       AS nb_orders,
  CASE WHEN COUNT(DISTINCT f.order_id)=0 THEN 0
       ELSE ROUND(SUM(f.total_ttc)/COUNT(DISTINCT f.order_id),2)
  END                                                              AS avg_basket,
  (SELECT COUNT(*) FROM refunds r JOIN f ON r.order_id=f.order_id) AS nb_refunds
FROM f
"""
kpi_result = session.sql(kpi_sql).collect()
if kpi_result:
    kpi = kpi_result[0]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CA TTC", f"{float(kpi['TOTAL_REVENUE']):,.2f} €")
    c2.metric("Commandes", int(kpi["NB_ORDERS"]))
    c3.metric("Panier moyen", f"{float(kpi['AVG_BASKET']):,.2f} €")
    c4.metric("Refunds", int(kpi["NB_REFUNDS"]))

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "◆ SAISONNALITÉ", "◇ TOP VENTES", "✦ AVIS", "◈ CLIENTS", 
    "◊ REMBOURSEMENTS", "◉ RFM", "◐ TEMPORALITÉ", "◑ DÉMOGRAPHIE"
])

# -----------------------------
# 1) Saisonnalité
# -----------------------------
with tab1:
    # --- Mensuel
    monthly_sql = f"""
    SELECT
      DATE_TRUNC('month', o.purchase_time) AS month,
      COUNT(DISTINCT o.order_id)           AS nb_orders,
      SUM(o.total_ttc)                     AS revenue_ttc
    FROM SALES_DATA.SALES_DATA.orders o
    JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id=ol.order_id
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id=pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id=p.product_id
    WHERE {WHERE}
    GROUP BY 1
    ORDER BY 1
    """
    df_month = session.sql(monthly_sql).to_pandas()
    st.subheader("Évolution mensuelle")

    if not df_month.empty:
        col_ca, col_cmd = st.columns(2)

        # Graphique CA mensuel
        with col_ca:
            st.caption("CA TTC (€) par mois")
            chart_ca = alt.Chart(df_month).mark_line(point=True).encode(
                x=alt.X('MONTH:T', title='', axis=alt.Axis(format='%b %Y', labelAngle=-45)),
                y=alt.Y('REVENUE_TTC:Q', title='CA TTC (€)'),
                tooltip=[
                    alt.Tooltip('MONTH:T', title='Mois', format='%B %Y'),
                    alt.Tooltip('REVENUE_TTC:Q', title='CA (€)', format=',.2f')
                ]
            ).properties(height=300).interactive()
            st.altair_chart(chart_ca, use_container_width=True)

        # Graphique Nb commandes mensuel
        with col_cmd:
            st.caption("Commandes par mois")
            chart_cmd = alt.Chart(df_month).mark_line(point=True).encode(
                x=alt.X('MONTH:T', title='', axis=alt.Axis(format='%b %Y', labelAngle=-45)),
                y=alt.Y('NB_ORDERS:Q', title='Commandes'),
                tooltip=[
                    alt.Tooltip('MONTH:T', title='Mois', format='%B %Y'),
                    alt.Tooltip('NB_ORDERS:Q', title='Commandes', format=',.0f')
                ]
            ).properties(height=300).interactive()
            st.altair_chart(chart_cmd, use_container_width=True)
    else:
        st.info("Aucune donnée sur la période/les filtres sélectionnés.")

    # --- Saisons
    season_sql = f"""
    SELECT
      CASE 
        WHEN MONTH(o.purchase_time) IN (3,4,5)   THEN 'Spring'
        WHEN MONTH(o.purchase_time) IN (6,7,8)   THEN 'Summer'
        WHEN MONTH(o.purchase_time) IN (9,10,11) THEN 'Autumn'
        ELSE 'Winter'
      END AS season,
      COUNT(DISTINCT o.order_id) AS nb_orders,
      SUM(o.total_ttc)           AS revenue_ttc
    FROM SALES_DATA.SALES_DATA.orders o
    JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id=ol.order_id
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id=pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id=p.product_id
    WHERE {WHERE}
    GROUP BY 1
    ORDER BY 1
    """
    df_season = session.sql(season_sql).to_pandas()
    st.subheader("Répartition saisonnière")

    if not df_season.empty:
        season_order = ['Spring', 'Summer', 'Autumn', 'Winter']
        col_ca2, col_cmd2 = st.columns(2)

        # Bar chart CA par saison
        with col_ca2:
            st.caption("CA TTC (€) par saison")
            chart_season_ca = alt.Chart(df_season).mark_bar().encode(
                x=alt.X('SEASON:N', title='', sort=season_order, axis=alt.Axis(labelAngle=0)),
                y=alt.Y('REVENUE_TTC:Q', title='CA TTC (€)'),
                tooltip=[
                    alt.Tooltip('SEASON:N', title='Saison'),
                    alt.Tooltip('REVENUE_TTC:Q', title='CA (€)', format=',.2f')
                ]
            ).properties(height=300)
            st.altair_chart(chart_season_ca, use_container_width=True)

        # Bar chart Commandes par saison
        with col_cmd2:
            st.caption("Commandes par saison")
            chart_season_cmd = alt.Chart(df_season).mark_bar().encode(
                x=alt.X('SEASON:N', title='', sort=season_order, axis=alt.Axis(labelAngle=0)),
                y=alt.Y('NB_ORDERS:Q', title='Commandes'),
                tooltip=[
                    alt.Tooltip('SEASON:N', title='Saison'),
                    alt.Tooltip('NB_ORDERS:Q', title='Commandes', format=',.0f')
                ]
            ).properties(height=300)
            st.altair_chart(chart_season_cmd, use_container_width=True)
    else:
        st.info("Aucune donnée sur la période/les filtres sélectionnés.")

# -----------------------------
# 2) Top ventes
# -----------------------------
with tab2:
    # Init des toggles (persistants)
    if "show_global_table" not in st.session_state:
        st.session_state.show_global_table = False
    if "show_size_table" not in st.session_state:
        st.session_state.show_size_table = False

    # =========================
    # Top ventes - GLOBAL
    # =========================
    st.subheader("Classement global")

    top_global_sql = f"""
    SELECT
      p.name,
      SUM(ol.quantity)       AS total_units,
      SUM(ol.line_total_ttc) AS revenue_ttc
    FROM SALES_DATA.SALES_DATA.order_lines ol
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
    JOIN SALES_DATA.SALES_DATA.orders o ON ol.order_id=o.order_id
    WHERE {WHERE}
    GROUP BY 1
    ORDER BY total_units DESC, revenue_ttc DESC
    LIMIT 10
    """
    df_top = session.sql(top_global_sql).to_pandas()
    df_top.columns = [c.upper() for c in df_top.columns]

    if not df_top.empty:
        # Meilleure vente (dans ce Top global)
        best = df_top.iloc[0]

        # Pire vente (sur tout le périmètre filtré)
        worst_sql = f"""
        SELECT name, total_units
        FROM (
          SELECT
            p.name,
            SUM(ol.quantity) AS total_units
          FROM SALES_DATA.SALES_DATA.order_lines ol
          JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
          JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
          JOIN SALES_DATA.SALES_DATA.orders o ON ol.order_id=o.order_id
          WHERE {WHERE}
          GROUP BY 1
        )
        ORDER BY total_units ASC
        LIMIT 1
        """
        df_worst = session.sql(worst_sql).to_pandas()
        df_worst.columns = [c.upper() for c in df_worst.columns]

        # Cartes élégantes (gradient)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #C9B99B 0%, #E8DFD0 100%);
                        border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
                <div style="color: #2C2825; font-size: 0.85rem; letter-spacing: 0.1em;
                            text-transform: uppercase; margin-bottom: 0.5rem;">
                    Meilleure vente
                </div>
                <div style="color: #2C2825; font-size: 1.5rem; font-weight: 300; margin-bottom: 0.5rem;">
                    {best['NAME']}
                </div>
                <div style="color: #8B7E74; font-size: 1.1rem;">
                    {int(best['TOTAL_UNITS'])} unités · {float(best['REVENUE_TTC']):,.2f} €
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if not df_worst.empty:
                worst = df_worst.iloc[0]
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #E8DFD0 0%, #F5F1E8 100%);
                            border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
                    <div style="color: #8B7E74; font-size: 0.85rem; letter-spacing: 0.1em;
                                text-transform: uppercase; margin-bottom: 0.5rem;">
                        Vente la plus faible
                    </div>
                    <div style="color: #2C2825; font-size: 1.5rem; font-weight: 300; margin-bottom: 0.5rem;">
                        {worst['NAME']}
                    </div>
                    <div style="color: #8B7E74; font-size: 1.1rem;">
                        {int(worst['TOTAL_UNITS'])} unités
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Bar chart des 10 meilleurs (CA)
        chart_top = alt.Chart(df_top).mark_bar().encode(
            x=alt.X('REVENUE_TTC:Q', title="Chiffre d'affaires (€)"),
            y=alt.Y('NAME:N', title='', sort='-x'),
            color=alt.value('#C9B99B'),
            tooltip=[
                alt.Tooltip('NAME:N', title='Produit'),
                alt.Tooltip('TOTAL_UNITS:Q', title='Unités vendues'),
                alt.Tooltip('REVENUE_TTC:Q', title='CA (€)', format=',.2f')
            ]
        ).properties(height=300)
        st.altair_chart(chart_top, use_container_width=True)

        # --- Toggle afficher/masquer tableau global
        if st.button(
            "Afficher / Masquer le tableau détaillé",
            key="toggle_global_table_btn",
            help="Utilise st.session_state pour mémoriser l'état d'affichage."
        ):
            st.session_state.show_global_table = not st.session_state.show_global_table

        if st.session_state.show_global_table:
            st.dataframe(df_top, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée sur la période/les filtres sélectionnés.")

    st.markdown("---")

    # =========================
    # Top ventes - PAR FORMAT (style harmonisé)
    # =========================
    st.subheader("Classement par format (Top 5)")

    top_by_size_sql = f"""
    SELECT
      pv.size_label,
      p.name,
      SUM(ol.quantity)       AS total_units,
      SUM(ol.line_total_ttc) AS revenue_ttc
    FROM SALES_DATA.SALES_DATA.order_lines ol
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
    JOIN SALES_DATA.SALES_DATA.orders o ON ol.order_id=o.order_id
    WHERE {WHERE}
    GROUP BY 1,2
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY pv.size_label
        ORDER BY SUM(ol.quantity) DESC, SUM(ol.line_total_ttc) DESC
    ) <= 5
    ORDER BY size_label, total_units DESC, revenue_ttc DESC
    """
    df_top_size = session.sql(top_by_size_sql).to_pandas()
    df_top_size.columns = [c.upper() for c in df_top_size.columns]

    if not df_top_size.empty:
        # Sélecteur de format
        sizes_avail = list(dict.fromkeys(df_top_size["SIZE_LABEL"].tolist()))
        selected_size = st.selectbox("Choisir un format", sizes_avail, index=0)

        df_size = df_top_size[df_top_size["SIZE_LABEL"] == selected_size].copy()

        # Meilleure & pire pour le format choisi
        best_size_row = df_size.iloc[0]

        worst_by_size_sql = f"""
        SELECT name, total_units
        FROM (
          SELECT
            p.name,
            SUM(ol.quantity) AS total_units
          FROM SALES_DATA.SALES_DATA.order_lines ol
          JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
          JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
          JOIN SALES_DATA.SALES_DATA.orders o ON ol.order_id = o.order_id
          WHERE {WHERE} AND pv.size_label = '{selected_size.replace("'", "''")}'
          GROUP BY 1
        )
        ORDER BY total_units ASC
        LIMIT 1
        """
        df_worst_size = session.sql(worst_by_size_sql).to_pandas()
        df_worst_size.columns = [c.upper() for c in df_worst_size.columns]

        colA, colB = st.columns(2)
        with colA:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #C9B99B 0%, #E8DFD0 100%);
                        border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
                <div style="color: #2C2825; font-size: 0.85rem; letter-spacing: 0.1em;
                            text-transform: uppercase; margin-bottom: 0.5rem;">
                    Meilleure vente ({selected_size})
                </div>
                <div style="color: #2C2825; font-size: 1.5rem; font-weight: 300; margin-bottom: 0.5rem;">
                    {best_size_row['NAME']}
                </div>
                <div style="color: #8B7E74; font-size: 1.1rem;">
                    {int(best_size_row['TOTAL_UNITS'])} unités · {float(best_size_row['REVENUE_TTC']):,.2f} €
                </div>
            </div>
            """, unsafe_allow_html=True)

        with colB:
            if not df_worst_size.empty:
                worst_size_row = df_worst_size.iloc[0]
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #E8DFD0 0%, #F5F1E8 100%);
                            border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
                    <div style="color: #8B7E74; font-size: 0.85rem; letter-spacing: 0.1em;
                                text-transform: uppercase; margin-bottom: 0.5rem;">
                        Vente la plus faible ({selected_size})
                    </div>
                    <div style="color: #2C2825; font-size: 1.5rem; font-weight: 300; margin-bottom: 0.5rem;">
                        {worst_size_row['NAME']}
                    </div>
                    <div style="color: #8B7E74; font-size: 1.1rem;">
                        {int(worst_size_row['TOTAL_UNITS'])} unités
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Bar chart Top 5 du format choisi (CA)
        chart_size = alt.Chart(df_size).mark_bar().encode(
            x=alt.X('REVENUE_TTC:Q', title="Chiffre d'affaires (€)"),
            y=alt.Y('NAME:N', title='', sort='-x'),
            color=alt.value('#C9B99B'),
            tooltip=[
                alt.Tooltip('NAME:N', title='Produit'),
                alt.Tooltip('TOTAL_UNITS:Q', title='Unités vendues'),
                alt.Tooltip('REVENUE_TTC:Q', title='CA (€)', format=',.2f')
            ]
        ).properties(height=300)
        st.altair_chart(chart_size, use_container_width=True)

        # --- Toggle afficher/masquer tableau Top 5 du format
        # On met une clé de bouton dépendante du format pour éviter les collisions de widgets
        if st.button(
            f"Afficher / Masquer le tableau (Top 5 – {selected_size})",
            key=f"toggle_size_table_btn_{selected_size}",
            help="Le statut du bouton est mémorisé dans st.session_state."
        ):
            st.session_state.show_size_table = not st.session_state.show_size_table

        if st.session_state.show_size_table:
            st.dataframe(df_size, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune vente par format sur la période/les filtres sélectionnés.")

# -----------------------------
# 3) Avis
# -----------------------------
with tab3:
    avg_review_sql = f"""
    SELECT
      ROUND(AVG(r.review_score),2) AS avg_review,
      COUNT(*)                     AS nb_reviews
    FROM SALES_DATA.SALES_DATA.reviews r
    JOIN SALES_DATA.SALES_DATA.orders o ON r.order_id = o.order_id
    JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
    WHERE {WHERE}
    """
    avg_result = session.sql(avg_review_sql).collect()
    if avg_result:
        df_avg = avg_result[0]
        st.subheader("Satisfaction globale")
        avg_val = float(df_avg['AVG_REVIEW']) if df_avg['AVG_REVIEW'] is not None else 0.0
        st.metric("✦ Note moyenne", f"{avg_val:.2f} / 5")
        st.caption(f"Nombre d'avis : {int(df_avg['NB_REVIEWS'] or 0)}")

    avg_by_prod_sql = f"""
    SELECT
      p.name,
      ROUND(AVG(r.review_score),2) AS avg_review,
      COUNT(*)                     AS nb_reviews
    FROM SALES_DATA.SALES_DATA.reviews r
    JOIN SALES_DATA.SALES_DATA.orders o ON r.order_id = o.order_id
    JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
    WHERE {WHERE}
    GROUP BY 1
    HAVING COUNT(*) >= 3
    ORDER BY avg_review DESC
    LIMIT 10
    """
    df_avg_prod = session.sql(avg_by_prod_sql).to_pandas()
    st.subheader("Produits les mieux notés")
    st.caption("Minimum 3 avis")
    st.dataframe(df_avg_prod, use_container_width=True, hide_index=True)

# -----------------------------
# 4) Clients
# -----------------------------
with tab4:
    top_clients_sql = f"""
    SELECT
      c.name,
      c.email,
      SUM(o.total_ttc)  AS total_spent,
      COUNT(o.order_id) AS nb_orders
    FROM SALES_DATA.SALES_DATA.orders o
    JOIN SALES_DATA.SALES_DATA.clients c ON o.client_id = c.client_id
    JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
    WHERE {WHERE}
    GROUP BY 1,2
    ORDER BY total_spent DESC
    LIMIT 10
    """
    df_clients = session.sql(top_clients_sql).to_pandas()
    st.subheader("Meilleurs clients")
    st.dataframe(df_clients, use_container_width=True, hide_index=True)

# -----------------------------
# 5) Refunds
# -----------------------------
with tab5:
    refund_sql = f"""
    WITH orders_in_scope AS (
      SELECT DISTINCT o.order_id
      FROM SALES_DATA.SALES_DATA.orders o
      JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
      JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
      JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
      WHERE {WHERE}
    ),
    refunded AS (
      SELECT DISTINCT order_id 
      FROM SALES_DATA.SALES_DATA.order_status_history 
      WHERE status='refunded'
    )
    SELECT
      (SELECT COUNT(*) FROM refunded r JOIN orders_in_scope o ON r.order_id=o.order_id) AS nb_refunded_orders,
      (SELECT COUNT(*) FROM orders_in_scope)                                           AS nb_orders_scope
    """
    refund_result = session.sql(refund_sql).collect()
    if refund_result:
        v = refund_result[0]
        nb_ref = int(v["NB_REFUNDED_ORDERS"] or 0)
        nb_all = int(v["NB_ORDERS_SCOPE"] or 0)
        rate = (100*nb_ref/nb_all) if nb_all else 0.0
        colA, colB = st.columns(2)
        colA.metric("Refunds (nb)", nb_ref)
        colB.metric("Refund rate (%)", f"{rate:.2f}")
    
    # Raisons de remboursement
    st.subheader("Raisons des remboursements")
    refund_reasons_sql = f"""
    SELECT 
      COALESCE(osh.refund_reason, 'Non spécifié') AS reason,
      COUNT(DISTINCT osh.order_id) AS nb_refunds
    FROM SALES_DATA.SALES_DATA.order_status_history osh
    JOIN SALES_DATA.SALES_DATA.orders o ON osh.order_id = o.order_id
    JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
    WHERE osh.status = 'refunded' AND {WHERE}
    GROUP BY 1
    ORDER BY 2 DESC
    """
    df_reasons = session.sql(refund_reasons_sql).to_pandas()
    if not df_reasons.empty:
        chart = alt.Chart(df_reasons).mark_bar().encode(
            x=alt.X('nb_refunds:Q', title='Nombre de remboursements'),
            y=alt.Y('reason:N', title='', sort='-x'),
            color=alt.value('#C9B99B'),
            tooltip=[
                alt.Tooltip('reason:N', title='Raison'),
                alt.Tooltip('nb_refunds:Q', title='Nombre')
            ]
        ).properties(height=250)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Aucun remboursement sur la période.")

# -----------------------------
# 6) Analyse RFM
# -----------------------------
with tab6:
    st.subheader("Segmentation RFM (Recency, Frequency, Monetary)")
    
    rfm_sql = f"""
    WITH client_metrics AS (
      SELECT 
        c.client_id,
        c.name,
        c.email,
        DATEDIFF(day, MAX(o.purchase_time), CURRENT_DATE()) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(o.total_ttc) AS monetary
      FROM SALES_DATA.SALES_DATA.clients c
      JOIN SALES_DATA.SALES_DATA.orders o ON c.client_id = o.client_id
      JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
      JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
      JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
      WHERE {WHERE}
      GROUP BY 1, 2, 3
    ),
    rfm_scores AS (
      SELECT 
        *,
        NTILE(5) OVER (ORDER BY recency_days) AS r_score,
        NTILE(5) OVER (ORDER BY frequency DESC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC) AS m_score
      FROM client_metrics
    ),
    rfm_segments AS (
      SELECT 
        *,
        CASE 
          WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'VIP'
          WHEN r_score >= 3 AND f_score >= 3 THEN 'Fidèles'
          WHEN r_score >= 4 AND f_score <= 2 THEN 'Nouveaux'
          WHEN r_score <= 2 AND f_score >= 3 THEN 'À risque'
          WHEN r_score <= 2 THEN 'Dormants'
          ELSE 'Occasionnels'
        END AS segment
      FROM rfm_scores
    )
    SELECT * FROM rfm_segments
    ORDER BY monetary DESC
    """
    
    df_rfm = session.sql(rfm_sql).to_pandas()
    
    if not df_rfm.empty:
        # Distribution des segments
        segment_counts = df_rfm['SEGMENT'].value_counts().reset_index()
        segment_counts.columns = ['SEGMENT', 'COUNT']
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Distribution des segments**")
            for _, row in segment_counts.iterrows():
                pct = 100 * row['COUNT'] / len(df_rfm)
                st.metric(row['SEGMENT'], f"{row['COUNT']} clients", f"{pct:.1f}%")
        
        with col2:
            # Scatter plot interactif Frequency vs Monetary
            scatter = alt.Chart(df_rfm).mark_circle(size=100, opacity=0.7).encode(
                x=alt.X('FREQUENCY:Q', title='Fréquence (nb commandes)'),
                y=alt.Y('MONETARY:Q', title='Montant dépensé (€)'),
                color=alt.Color('SEGMENT:N', 
                              scale=alt.Scale(domain=['VIP', 'Fidèles', 'Nouveaux', 'À risque', 'Dormants', 'Occasionnels'],
                                            range=['#2C2825', '#8B7E74', '#C9B99B', '#E8DFD0', '#F5F1E8', '#D4C5B0']),
                              legend=alt.Legend(title='Segment')),
                tooltip=[
                    alt.Tooltip('NAME:N', title='Client'),
                    alt.Tooltip('SEGMENT:N', title='Segment'),
                    alt.Tooltip('FREQUENCY:Q', title='Commandes'),
                    alt.Tooltip('MONETARY:Q', title='CA (€)', format=',.2f'),
                    alt.Tooltip('RECENCY_DAYS:Q', title='Jours depuis dernier achat')
                ]
            ).properties(height=400).interactive()
            
            st.altair_chart(scatter, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Détail des clients par segment")
        
        selected_segment = st.selectbox("Filtrer par segment", ['Tous'] + list(segment_counts['SEGMENT']))
        
        if selected_segment == 'Tous':
            df_display = df_rfm[['NAME', 'EMAIL', 'SEGMENT', 'RECENCY_DAYS', 'FREQUENCY', 'MONETARY']]
        else:
            df_display = df_rfm[df_rfm['SEGMENT'] == selected_segment][['NAME', 'EMAIL', 'SEGMENT', 'RECENCY_DAYS', 'FREQUENCY', 'MONETARY']]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée RFM disponible sur la période.")

# -----------------------------
# 7) Heatmap Temporelle
# -----------------------------
with tab7:
    st.subheader("Patterns temporels des achats")
    
    # Heatmap jour de semaine × heure
    temporal_sql = f"""
    SELECT 
      o.purchase_dow AS day_of_week,
      HOUR(o.purchase_time) AS hour_of_day,
      COUNT(DISTINCT o.order_id) AS nb_orders
    FROM SALES_DATA.SALES_DATA.orders o
    JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
    WHERE {WHERE}
    GROUP BY 1, 2
    ORDER BY 1, 2
    """
    
    df_temporal = session.sql(temporal_sql).to_pandas()
    
    if not df_temporal.empty:
        # Mapper les jours de la semaine
        day_mapping = {1: 'Lundi', 2: 'Mardi', 3: 'Mercredi', 4: 'Jeudi', 
                      5: 'Vendredi', 6: 'Samedi', 7: 'Dimanche'}
        df_temporal['DAY_NAME'] = df_temporal['DAY_OF_WEEK'].map(day_mapping)
        
        # Heatmap
        heatmap = alt.Chart(df_temporal).mark_rect().encode(
            x=alt.X('HOUR_OF_DAY:O', title='Heure de la journée'),
            y=alt.Y('DAY_NAME:N', title='', sort=list(day_mapping.values())),
            color=alt.Color('NB_ORDERS:Q', 
                          scale=alt.Scale(scheme='goldorange'),
                          legend=alt.Legend(title='Commandes')),
            tooltip=[
                alt.Tooltip('DAY_NAME:N', title='Jour'),
                alt.Tooltip('HOUR_OF_DAY:O', title='Heure'),
                alt.Tooltip('NB_ORDERS:Q', title='Commandes')
            ]
        ).properties(height=300)
        
        st.altair_chart(heatmap, use_container_width=True)
        
        st.caption("💡 Cette heatmap montre les moments de la semaine où vos clients achètent le plus")
    else:
        st.info("Aucune donnée temporelle disponible.")
    
    # Distribution par jour de la semaine
    st.subheader("Répartition par jour de la semaine")
    dow_sql = f"""
    SELECT 
      o.purchase_dow,
      COUNT(DISTINCT o.order_id) AS nb_orders,
      SUM(o.total_ttc) AS revenue_ttc
    FROM SALES_DATA.SALES_DATA.orders o
    JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
    WHERE {WHERE}
    GROUP BY 1
    ORDER BY 1
    """
    df_dow = session.sql(dow_sql).to_pandas()
    
    if not df_dow.empty:
        df_dow['DAY_NAME'] = df_dow['PURCHASE_DOW'].map(day_mapping)
        
        bar_chart = alt.Chart(df_dow).mark_bar().encode(
            x=alt.X('DAY_NAME:N', title='', sort=list(day_mapping.values())),
            y=alt.Y('NB_ORDERS:Q', title='Nombre de commandes'),
            color=alt.value('#C9B99B'),
            tooltip=[
                alt.Tooltip('DAY_NAME:N', title='Jour'),
                alt.Tooltip('NB_ORDERS:Q', title='Commandes'),
                alt.Tooltip('REVENUE_TTC:Q', title='CA (€)', format=',.2f')
            ]
        ).properties(height=250)
        
        st.altair_chart(bar_chart, use_container_width=True)

# -----------------------------
# 8) Analyse Démographique
# -----------------------------
with tab8:
    st.subheader("Profil démographique des clients")
    
    # Distribution par genre et tranche d'âge
    demo_sql = f"""
    SELECT 
      c.sex,
      CASE 
        WHEN DATEDIFF(year, c.date_of_birth, CURRENT_DATE()) < 25 THEN '18-24'
        WHEN DATEDIFF(year, c.date_of_birth, CURRENT_DATE()) < 35 THEN '25-34'
        WHEN DATEDIFF(year, c.date_of_birth, CURRENT_DATE()) < 45 THEN '35-44'
        WHEN DATEDIFF(year, c.date_of_birth, CURRENT_DATE()) < 55 THEN '45-54'
        WHEN DATEDIFF(year, c.date_of_birth, CURRENT_DATE()) < 65 THEN '55-64'
        ELSE '65+'
      END AS age_group,
      COUNT(DISTINCT c.client_id) AS nb_clients,
      COUNT(DISTINCT o.order_id) AS nb_orders,
      SUM(o.total_ttc) AS revenue_ttc,
      AVG(o.total_ttc) AS avg_basket
    FROM SALES_DATA.SALES_DATA.clients c
    JOIN SALES_DATA.SALES_DATA.orders o ON c.client_id = o.client_id
    JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
    JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
    JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
    WHERE {WHERE}
    GROUP BY 1, 2
    ORDER BY 1, 2
    """
    
    df_demo = session.sql(demo_sql).to_pandas()
    
    if not df_demo.empty:
        # Mapper les genres
        sex_mapping = {'m': 'Homme', 'f': 'Femme', 'x': 'Autre'}
        df_demo['GENDER'] = df_demo['SEX'].map(sex_mapping)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CA par genre et âge
            heatmap_demo = alt.Chart(df_demo).mark_rect().encode(
                x=alt.X('AGE_GROUP:N', title='Tranche d\'âge', 
                       sort=['18-24', '25-34', '35-44', '45-54', '55-64', '65+']),
                y=alt.Y('GENDER:N', title=''),
                color=alt.Color('REVENUE_TTC:Q', 
                              scale=alt.Scale(scheme='goldorange'),
                              legend=alt.Legend(title='CA (€)')),
                tooltip=[
                    alt.Tooltip('GENDER:N', title='Genre'),
                    alt.Tooltip('AGE_GROUP:N', title='Âge'),
                    alt.Tooltip('NB_CLIENTS:Q', title='Clients'),
                    alt.Tooltip('REVENUE_TTC:Q', title='CA (€)', format=',.2f'),
                    alt.Tooltip('AVG_BASKET:Q', title='Panier moyen (€)', format=',.2f')
                ]
            ).properties(height=200, title='Chiffre d\'affaires par profil')
            
            st.altair_chart(heatmap_demo, use_container_width=True)
        
        with col2:
            # Panier moyen par segment
            bar_basket = alt.Chart(df_demo).mark_bar().encode(
                x=alt.X('AVG_BASKET:Q', title='Panier moyen (€)'),
                y=alt.Y('AGE_GROUP:N', title='', 
                       sort=['18-24', '25-34', '35-44', '45-54', '55-64', '65+']),
                color=alt.Color('GENDER:N', 
                              scale=alt.Scale(range=['#C9B99B', '#8B7E74', '#E8DFD0']),
                              legend=alt.Legend(title='Genre')),
                tooltip=[
                    alt.Tooltip('GENDER:N', title='Genre'),
                    alt.Tooltip('AGE_GROUP:N', title='Âge'),
                    alt.Tooltip('AVG_BASKET:Q', title='Panier moyen (€)', format=',.2f')
                ]
            ).properties(height=200, title='Panier moyen par profil')
            
            st.altair_chart(bar_basket, use_container_width=True)
        
        st.markdown("---")
        
        # Préférences olfactives par profil
        st.subheader("Préférences olfactives par profil")
        
        pref_sql = f"""
        SELECT 
          c.sex,
          CASE 
            WHEN DATEDIFF(year, c.date_of_birth, CURRENT_DATE()) < 35 THEN 'Jeune'
            WHEN DATEDIFF(year, c.date_of_birth, CURRENT_DATE()) < 55 THEN 'Adulte'
            ELSE 'Senior'
          END AS age_category,
          p.category,
          p.gender AS product_gender,
          COUNT(DISTINCT o.order_id) AS nb_orders,
          SUM(ol.line_total_ttc) AS revenue_ttc
        FROM SALES_DATA.SALES_DATA.clients c
        JOIN SALES_DATA.SALES_DATA.orders o ON c.client_id = o.client_id
        JOIN SALES_DATA.SALES_DATA.order_lines ol ON o.order_id = ol.order_id
        JOIN SALES_DATA.SALES_DATA.product_variants pv ON ol.product_variant_id = pv.product_variant_id
        JOIN SALES_DATA.SALES_DATA.products p ON pv.product_id = p.product_id
        WHERE {WHERE}
        GROUP BY 1, 2, 3, 4
        ORDER BY 6 DESC
        """
        
        df_pref = session.sql(pref_sql).to_pandas()
        
        if not df_pref.empty:
            df_pref['GENDER'] = df_pref['SEX'].map(sex_mapping)
            
            # Top catégories par profil
            top_cat = alt.Chart(df_pref).mark_bar().encode(
                x=alt.X('REVENUE_TTC:Q', title='CA (€)'),
                y=alt.Y('CATEGORY:N', title='', sort='-x'),
                color=alt.Color('AGE_CATEGORY:N', 
                              scale=alt.Scale(range=['#C9B99B', '#8B7E74', '#E8DFD0']),
                              legend=alt.Legend(title='Âge')),
                column=alt.Column('GENDER:N', title=''),
                tooltip=[
                    alt.Tooltip('GENDER:N', title='Client'),
                    alt.Tooltip('AGE_CATEGORY:N', title='Âge'),
                    alt.Tooltip('CATEGORY:N', title='Catégorie'),
                    alt.Tooltip('REVENUE_TTC:Q', title='CA (€)', format=',.2f')
                ]
            ).properties(height=300, width=200)
            
            st.altair_chart(top_cat)
        
        st.dataframe(df_demo, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée démographique disponible.")