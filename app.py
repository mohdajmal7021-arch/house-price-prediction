from __future__ import annotations

import sys
from pathlib import Path

import re
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu

from utils.predictor import (
    predict_price,
    get_dashboard_metrics,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.auth_db import init_db, register_user, login_user as auth_login

APP_TITLE = "HomeValue AI"
APP_SUBTITLE = "Intelligent House Price Prediction System"


def initialize_state():
    init_db()
    defaults = {
        "history": [],
        "theme_mode": "light",
        "selected_nav": "predict",
        "logged_in": False,
        "user": None,
        "page": "landing",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def apply_premium_theme():
    theme = st.session_state.theme_mode

    if theme == "dark":
        bg_primary = "#0f0f1e"
        bg_secondary = "#1a1a2e"
        card_bg = "rgba(26, 26, 46, 0.95)"
        text_primary = "#ffffff"
        text_secondary = "#a0a0c0"
        accent = "#3b82f6"
        accent_secondary = "#10b981"
        success = "#10b981"
        warning = "#f59e0b"
        error = "#ef4444"
        border = "rgba(59, 130, 246, 0.2)"
    else:
        bg_primary = "#f8fafc"
        bg_secondary = "#ffffff"
        card_bg = "rgba(255, 255, 255, 0.95)"
        text_primary = "#0f172a"
        text_secondary = "#475569"
        accent = "#3b82f6"
        accent_secondary = "#10b981"
        success = "#10b981"
        warning = "#f59e0b"
        error = "#ef4444"
        border = "rgba(59, 130, 246, 0.1)"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {bg_primary};
            color: {text_primary};
        }}
        .glass-card {{
            background: {card_bg};
            backdrop-filter: blur(10px);
            border: 1px solid {border};
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }}
        .glass-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.15);
            border-color: {accent};
        }}
        .hero-section {{
            background: linear-gradient(135deg, {accent}20 0%, {accent_secondary}20 100%);
            border: 1px solid {border};
            border-radius: 25px;
            padding: 2rem;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }}
        .hero-section::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, {accent}10 0%, transparent 70%);
        }}
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        .hero-title {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, {accent} 0%, {accent_secondary} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            position: relative;
            z-index: 1;
        }}
        .hero-subtitle {{
            font-size: 1.1rem;
            color: {text_secondary};
            position: relative;
            z-index: 1;
        }}
        .metric-card {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 15px;
            padding: 1.25rem;
            text-align: center;
            transition: all 0.3s ease;
        }}
        .metric-card:hover {{
            transform: scale(1.05);
            border-color: {accent};
            box-shadow: 0 5px 20px rgba(59, 130, 246, 0.2);
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, {accent} 0%, {accent_secondary} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .metric-label {{
            font-size: 0.85rem;
            color: {text_secondary};
            margin-top: 0.5rem;
        }}
        .price-display {{
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, {accent} 0%, {accent_secondary} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            padding: 1rem 0;
        }}
        .stNumberInput > div > div > input,
        .stSlider > div > div > div,
        .stSelectbox > div > div {{
            background: {card_bg};
            border-color: {border};
            border-radius: 10px;
        }}
        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, {accent} 0%, {accent_secondary} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .result-card {{
            background: linear-gradient(135deg, {accent}15 0%, {accent_secondary}15 100%);
            border: 1px solid {accent}40;
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            animation: slideIn 0.5s ease-out;
        }}
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: {bg_secondary};
            border-radius: 10px;
        }}
        ::-webkit-scrollbar-thumb {{
            background: {accent};
            border-radius: 10px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {accent_secondary};
        }}
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .fade-in-up {{
            animation: fadeInUp 0.6s ease-out;
        }}
        .auth-container {{ max-width: 420px; margin: 4rem auto; padding: 2rem; background: {card_bg}; backdrop-filter: blur(20px); border: 1px solid {border}; border-radius: 24px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }}
        .auth-title {{ font-size: 2rem; font-weight: 800; text-align: center; background: linear-gradient(135deg, {accent} 0%, {accent_secondary} 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }}
        .auth-subtitle {{ text-align: center; color: {text_secondary}; margin-bottom: 2rem; }}
        .auth-divider {{ border: none; height: 1px; background: linear-gradient(90deg, transparent, {accent}, transparent); margin: 2rem 0; }}
        .landing-section {{ text-align: center; padding: 3rem 1rem; }}
        .landing-title {{ font-size: 3.5rem; font-weight: 900; background: linear-gradient(135deg, {accent} 0%, {accent_secondary} 50%, {success} 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem; }}
        .landing-subtitle {{ font-size: 1.3rem; color: {text_secondary}; max-width: 600px; margin: 0 auto 2.5rem; }}
        .landing-card {{ background: {card_bg}; border: 1px solid {border}; border-radius: 20px; padding: 2rem; transition: all 0.3s; height: 100%; }}
        .landing-card:hover {{ transform: translateY(-8px); border-color: {accent}; box-shadow: 0 20px 40px rgba(59,130,246,0.15); }}
        .home-header {{ display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; margin-bottom: 2rem; border-bottom: 1px solid {border}; }}
        .home-welcome {{ font-size: 2.2rem; font-weight: 800; }}
        .home-welcome span {{ background: linear-gradient(135deg, {accent} 0%, {accent_secondary} 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_logout_sidebar():
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "landing"
            st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown("### 🏠 HomeValue AI")
        st.markdown("---")

        options = ["🏠 Home", "🎯 Predict", "📊 Analytics", "📜 History", "ℹ️ About"]
        icons = ["house", "cursor", "graph-up", "clock-history", "info-circle"]

        selected = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background": "transparent"},
                "icon": {"color": "#3b82f6", "font-size": "1.2rem"},
                "nav-link": {
                    "font-size": "1rem",
                    "text-align": "left",
                    "margin": "0.5rem 0",
                    "border-radius": "10px",
                    "transition": "all 0.3s ease",
                },
                "nav-link-hover": {
                    "background": "rgba(59, 130, 246, 0.1)",
                    "transform": "translateX(5px)",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #3b82f6 0%, #10b981 100%)",
                },
            },
        )

        st.markdown("---")

        theme_mode = st.toggle("🌙 Dark Mode", value=st.session_state.theme_mode == "dark")
        st.session_state.theme_mode = "dark" if theme_mode else "light"

        st.markdown("---")
        st.markdown("### 📈 Quick Stats")
        metrics = get_dashboard_metrics()
        st.metric("Algorithm", metrics.get("algorithm", "Unknown"))
        st.metric("R2 Score", f"{metrics.get('r2_score', 0):.2%}")
        st.metric("Total Predictions", len(st.session_state.history))

        return selected


def render_hero():
    st.markdown(
        f"""
        <div class="hero-section fade-in-up">
            <h1 class="hero-title">HomeValue AI</h1>
            <p class="hero-subtitle">Intelligent House Price Prediction System</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard():
    metrics = get_dashboard_metrics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.get('algorithm', 'RR')}</div>
                <div class="metric-label">🤖 Algorithm</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        r2 = metrics.get('r2_score', 0)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{r2:.1%}</div>
                <div class="metric-label">📈 R2 Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.get('dataset_rows', 0):,}</div>
                <div class="metric-label">📊 Training Records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        features = len(metrics.get('features', []))
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{features}</div>
                <div class="metric-label">🔧 Features Used</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_form():
    st.markdown('<div class="section-title">🏡 Property Details</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📐 Size & Layout", "🏚️ Condition & Age"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            bedrooms = st.number_input("🛏️ Bedrooms", min_value=0.0, max_value=20.0, value=3.0, step=1.0)
            bathrooms = st.number_input("🚿 Bathrooms", min_value=0.0, max_value=20.0, value=2.0, step=0.25)
            sqft_living = st.number_input("📐 Living Area (sqft)", min_value=100.0, max_value=15000.0, value=1800.0, step=100.0)
            sqft_lot = st.number_input("📏 Lot Size (sqft)", min_value=500.0, max_value=500000.0, value=8000.0, step=500.0)
        with col2:
            floors = st.number_input("🏗️ Floors", min_value=0.5, max_value=5.0, value=1.5, step=0.5)
            sqft_above = st.number_input("🏠 Above Ground (sqft)", min_value=100.0, max_value=15000.0, value=1400.0, step=100.0)
            sqft_basement = st.number_input("🧱 Basement (sqft)", min_value=0.0, max_value=10000.0, value=0.0, step=100.0)
            waterfront = st.selectbox("🌊 Waterfront", [0, 1], format_func=lambda x: "Yes" if x else "No")

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            yr_built = st.number_input("🏗️ Year Built", min_value=1800, max_value=2026, value=1990)
            condition = st.select_slider("⭐ Condition", options=[1, 2, 3, 4, 5], value=3,
                                         format_func=lambda x: f"{x} - {'Poor' if x==1 else 'Fair' if x==2 else 'Average' if x==3 else 'Good' if x==4 else 'Excellent'}")
        with col2:
            yr_renovated = st.number_input("🔨 Year Renovated (0 if never)", min_value=0, max_value=2026, value=0)
            view = st.select_slider("👁️ View Rating", options=[0, 1, 2, 3, 4], value=0,
                                    format_func=lambda x: f"{x} - {'None' if x==0 else 'Fair' if x==1 else 'Average' if x==2 else 'Good' if x==3 else 'Excellent'}")

    st.markdown('</div>', unsafe_allow_html=True)

    return {
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "sqft_living": sqft_living,
        "sqft_lot": sqft_lot,
        "floors": floors,
        "waterfront": waterfront,
        "view": view,
        "condition": condition,
        "sqft_above": sqft_above,
        "sqft_basement": sqft_basement,
        "yr_built": yr_built,
        "yr_renovated": yr_renovated,
    }


def format_price(price):
    if price >= 1_000_000:
        return f"${price / 1_000_000:,.2f}M"
    return f"${price:,.0f}"


def render_prediction(data):
    if st.button("🏠 Estimate Property Value", use_container_width=True, type="primary"):
        with st.spinner("Analyzing property data..."):
            result = predict_price(
                bedrooms=data["bedrooms"],
                bathrooms=data["bathrooms"],
                sqft_living=data["sqft_living"],
                sqft_lot=data["sqft_lot"],
                floors=data["floors"],
                waterfront=data["waterfront"],
                view=data["view"],
                condition=data["condition"],
                sqft_above=data["sqft_above"],
                sqft_basement=data["sqft_basement"],
                yr_built=data["yr_built"],
                yr_renovated=data["yr_renovated"],
            )

            price = result["predicted_price"]

            add_history(price, data["sqft_living"])

            st.markdown('<div class="result-card fade-in-up">', unsafe_allow_html=True)

            st.markdown(f"### Estimated Property Value")
            st.markdown(f'<div class="price-display">{format_price(price)}</div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Price per sqft", f"${price / max(data['sqft_living'], 1):,.0f}")
            with col2:
                st.metric("Living Area", f"{data['sqft_living']:,.0f} sqft")
            with col3:
                st.metric("Property Age", f"{2026 - data['yr_built']} years")

            st.markdown("---")
            st.markdown("### 📊 Property Value Breakdown")

            comparison_data = {
                "Feature": ["Bedrooms", "Bathrooms", "Living Area", "Lot Size", "Floors", "Condition"],
                "Value": [
                    f"{data['bedrooms']:.0f}",
                    f"{data['bathrooms']:.2f}",
                    f"{data['sqft_living']:,.0f} sqft",
                    f"{data['sqft_lot']:,.0f} sqft",
                    f"{data['floors']:.1f}",
                    f"{data['condition']}/5",
                ]
            }
            st.table(pd.DataFrame(comparison_data))

            st.markdown('</div>', unsafe_allow_html=True)


def add_history(price, sqft_living):
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "price": round(price, 2),
        "sqft_living": sqft_living,
    })


def history_to_csv():
    df = pd.DataFrame(st.session_state.history)
    return df.to_csv(index=False).encode("utf-8")


def render_history():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📜 Prediction History</div>', unsafe_allow_html=True)

    if st.session_state.history:
        history_df = pd.DataFrame(st.session_state.history)

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": "⏰ Time",
                "price": st.column_config.NumberColumn(
                    "💰 Estimated Price", format="$%.0f"
                ),
                "sqft_living": st.column_config.NumberColumn(
                    "📐 Living Area", format="%.0f sqft"
                ),
            }
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Predictions", len(history_df))
        with col2:
            avg_price = history_df['price'].mean()
            st.metric("Average Price", f"${avg_price:,.0f}")
        with col3:
            max_price = history_df['price'].max()
            st.metric("Highest Estimate", f"${max_price:,.0f}")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                "📥 Download History CSV",
                data=history_to_csv(),
                file_name="house_price_predictions.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("No predictions made yet. Start by estimating a property value!")
    st.markdown('</div>', unsafe_allow_html=True)


def render_analytics():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Analytics Dashboard</div>', unsafe_allow_html=True)

    if st.session_state.history:
        history_df = pd.DataFrame(st.session_state.history)

        col1, col2 = st.columns(2)

        with col1:
            avg_price = history_df['price'].mean()
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">${avg_price:,.0f}</div>
                    <div class="metric-label">💰 Average Estimated Price</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            avg_ppsqft = (history_df['price'] / history_df['sqft_living']).mean()
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">${avg_ppsqft:,.0f}</div>
                    <div class="metric-label">📐 Avg Price per sqft</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("### 📈 Price Trends")
        fig = px.line(
            history_df,
            x='timestamp',
            y='price',
            title='Estimated Property Values Over Time',
            color_discrete_sequence=['#3b82f6'],
            markers=True,
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Time",
            yaxis_title="Price ($)",
            height=400,
        )
        fig.update_yaxes(tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            fig_hist = px.histogram(
                history_df,
                x='price',
                nbins=20,
                title='Price Distribution',
                color_discrete_sequence=['#3b82f6']
            )
            fig_hist.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
            )
            fig_hist.update_xaxes(tickprefix="$")
            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            fig_scatter = px.scatter(
                history_df,
                x='sqft_living',
                y='price',
                title='Price vs Living Area',
                color_discrete_sequence=['#10b981'],
                trendline="ols",
            )
            fig_scatter.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
            )
            fig_scatter.update_xaxes(title="Living Area (sqft)")
            fig_scatter.update_yaxes(title="Price ($)", tickprefix="$")
            st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No data available. Make some predictions to see analytics!")


def render_about():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ℹ️ About HomeValue AI</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 🤖 Intelligent House Price Prediction System

    HomeValue AI uses machine learning (Ridge Regression) to estimate property values based on multiple factors:

    #### 📐 Size & Layout
    - Bedrooms, Bathrooms
    - Living Area & Lot Size
    - Floors, Above Ground Area
    - Basement Size
    - Waterfront Location

    #### 📍 Location
    - City
    - State/Zip Code

    #### 🏚️ Condition & Age
    - Year Built & Renovated
    - Property Condition & View Rating

    ### 🎯 How It Works

    1. **Enter property details** across size, location, and condition
    2. **Our ML model** analyzes against historical sales data
    3. **Get instant valuation** with price estimate
    4. **View per-square-foot analysis** and property insights

    ### 📊 Model Performance

    - **Algorithm:** Ridge Regression
    - **R2 Score:** ~70-75% on test data
    - **Features:** 10+ key parameters + location encoding
    - **Training Data:** 4600+ property records from King County, WA

    ### 💡 Tips for Accurate Valuation

    - Provide accurate square footage
    - Specify correct location (city/ZIP)
    - Include recent renovation year
    - Note waterfront or premium view properties

    ---

    **Developed with** ❤️ **using Streamlit & Scikit-learn**
    """)

    st.markdown('</div>', unsafe_allow_html=True)


def render_landing():
    ts_color = "#a0a0c0" if st.session_state.theme_mode == "dark" else "#475569"
    st.markdown(
        f"""
        <div class="landing-section fade-in-up">
            <div style="font-size: 4rem;">🏠</div>
            <h1 class="landing-title">HomeValue AI</h1>
            <p class="landing-subtitle">Intelligent House Price Prediction — powered by machine learning. Estimate property values, analyze market trends, and make data-driven real estate decisions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="landing-card">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                <h3>Gradient Boosting</h3>
                <p style="color: {ts_color};">State-of-the-art gradient boosting regression for highly accurate price predictions.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="landing-card">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🏡</div>
                <h3>Property Analysis</h3>
                <p style="color: {ts_color};">Comprehensive feature analysis including size, location, condition, and amenities.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="landing-card">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h3>Market Insights</h3>
                <p style="color: {ts_color};">Visual analytics and trends to understand market dynamics and property values.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="auth-divider">', unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("🔐 Login", use_container_width=True, type="primary"):
            st.session_state.page = "login"
            st.rerun()
        if st.button("📝 Register", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()


def render_login():
    st.markdown(
        f"""
        <div class="auth-container fade-in-up">
            <div style="text-align: center; font-size: 3rem;">🏠</div>
            <h2 class="auth-title">Welcome Back</h2>
            <p class="auth-subtitle">Sign in to HomeValue AI</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                success, result = auth_login(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.user = result
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error(result)

    st.markdown('<hr class="auth-divider">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()


def render_register():
    st.markdown(
        f"""
        <div class="auth-container fade-in-up">
            <div style="text-align: center; font-size: 3rem;">🏠</div>
            <h2 class="auth-title">Create Account</h2>
            <p class="auth-subtitle">Join HomeValue AI today</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("register_form", clear_on_submit=True):
        username = st.text_input("👤 Username", placeholder="Choose a username")
        email = st.text_input("📧 Email", placeholder="Enter your email")
        password = st.text_input("🔒 Password", type="password", placeholder="Create a password")
        confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
        submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if submitted:
            if not username or not email or not password or not confirm:
                st.error("Please fill in all fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                success, msg = register_user(username, email, password)
                if success:
                    st.success(msg)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown('<hr class="auth-divider">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()


def render_home():
    metrics = get_dashboard_metrics()

    st.markdown(
        f"""
        <div class="home-header">
            <div class="home-welcome">Welcome, <span>{st.session_state.user['username']}</span> 👋</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.get('algorithm', 'GBR')}</div>
                <div class="metric-label">🤖 Algorithm</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        r2 = metrics.get('r2_score', 0)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{r2:.1%}</div>
                <div class="metric-label">📈 R2 Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.get('dataset_rows', 0):,}</div>
                <div class="metric-label">📊 Training Records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(st.session_state.history)}</div>
                <div class="metric-label">📋 Analyses</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        if st.button("🎯 Go to Predict", use_container_width=True):
            st.session_state.selected_nav = "predict"
            st.rerun()
    with col_b:
        if st.button("📊 Go to Analytics", use_container_width=True):
            st.session_state.selected_nav = "analytics"
            st.rerun()


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    initialize_state()
    apply_premium_theme()

    if not st.session_state.logged_in:
        if st.session_state.page == "landing":
            render_landing()
        elif st.session_state.page == "login":
            render_login()
        elif st.session_state.page == "register":
            render_register()
        else:
            render_landing()
        return

    selected_page = render_sidebar()
    render_logout_sidebar()

    if selected_page != "ℹ️ About" and selected_page != "🏠 Home":
        render_hero()

    if selected_page == "🏠 Home":
        render_home()

    if selected_page == "🎯 Predict":
        render_dashboard()
        st.divider()
        property_data = render_form()
        render_prediction(property_data)

    elif selected_page == "📊 Analytics":
        render_analytics()

    elif selected_page == "📜 History":
        render_history()

    elif selected_page == "ℹ️ About":
        render_about()


if __name__ == "__main__":
    main()
