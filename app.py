"""
=============================================================
  app.py
  Fake Website Detection System
  Role: Streamlit web UI — enter URL → get prediction
  Run: streamlit run app.py
=============================================================
"""

import os, pickle, sys
import pandas as pd
import numpy as np
import streamlit as st
from PIL import Image

# ── Make sibling modules importable regardless of cwd ───────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_extraction import extract_features
from auth import require_login

# ─────────────────────────────────────────────────────────────
# Page config (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PhishGuard — Fake Website Detector",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# Custom CSS — cyberpunk / dark-terminal aesthetic
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;600;800&display=swap');

/* ── Root variables ── */
:root {
    --bg:       #EEE4DA;
    --card:     #FFFFFF;
    --border:   #857861;
    --cyan:     #4D0E13;
    --red:      #E43B44;
    --green:    #2E8B57;
    --gold:     #DAA520;
    --text:     #4D0E13;
    --muted:    #857861;
    --radius:   12px;
    --mono:     'Share Tech Mono', monospace;
    --sans:     'Exo 2', sans-serif;
}

/* ── Base ── */
html, body, .stApp, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans);
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 780px; }

/* ── Title banner ── */
.banner {
    background-color: #4D0E13;
    color: #C8A49F;
    text-align: center;
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.banner h1 {
    font-family: var(--sans);
    font-weight: 800;
    font-size: 2.5rem;
    color: #C8A49F;
    margin: 0;
}
.banner h1 span { color: #E7D4BB; }
.banner p { display: none; }

/* ── Input styling ── */
.stTextInput > div > div > input {
    background-color: #91989B !important;
    border: 2px solid #234C58 !important;
    border-radius: 8px !important;
    color: #234C58 !important;
    font-family: var(--mono) !important;
    font-size: .95rem !important;
    padding: .6rem 1rem !important;
    transition: border-color .2s;
}
.stTextInput > div > div > input:focus {
    border-color: #4D0E13 !important;
}
.stTextInput > div > div > input::placeholder {
    color: #234C58 !important;
    opacity: 0.7;
}

/* ── Button ── */
.stButton > button {
    background-color: #29281E !important;
    color: #E7D4BB !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: var(--sans) !important;
    font-weight: bold !important;
    font-size: 1rem !important;
    padding: .6rem 2.5rem !important;
    cursor: pointer !important;
    transition: 0.3s !important;
}
.stButton > button:hover {
    background-color: #171610 !important;
    color: #FFFFFF !important;
}

/* ── Result cards ── */
.result-card {
    border-radius: var(--radius);
    padding: 1.5rem 1.8rem;
    margin: 1.2rem 0;
    border-left: 5px solid;
    position: relative;
    overflow: hidden;
}
.result-card.legit {
    background: linear-gradient(135deg, rgba(0,230,118,.08), rgba(0,0,0,0));
    border-color: var(--green);
}
.result-card.fake {
    background: linear-gradient(135deg, rgba(255,23,68,.10), rgba(0,0,0,0));
    border-color: var(--red);
}
.result-icon { font-size: 2.5rem; margin-bottom: .4rem; }
.result-label {
    font-family: var(--sans);
    font-weight: 800;
    font-size: 1.7rem;
    margin: 0;
}
.result-label.legit { color: var(--green); }
.result-label.fake  { color: var(--red); }
.result-sub { color: var(--muted); font-family: var(--mono); font-size: .83rem; margin-top: .2rem; }

/* ── Confidence bar ── */
.conf-wrap { margin-top: 1rem; }
.conf-label { font-size: .82rem; color: var(--muted); font-family: var(--mono); margin-bottom: .3rem; }
.conf-bar-bg {
    background: var(--border);
    border-radius: 20px;
    height: 10px;
    overflow: hidden;
}
.conf-bar-fill {
    height: 100%;
    border-radius: 20px;
    transition: width .8s ease;
}
.conf-pct {
    font-family: var(--mono);
    font-size: 1.15rem;
    font-weight: 700;
    margin-top: .4rem;
}

/* ── Feature pill grid ── */
.feat-grid { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .8rem; }
.feat-pill {
    font-family: var(--mono);
    font-size: .77rem;
    padding: .25rem .7rem;
    border-radius: 20px;
    border: 1px solid var(--border);
    background: var(--card);
    white-space: nowrap;
}
.feat-pill.warn { border-color: var(--red);  color: var(--red);  background: rgba(255,23,68,.08); }
.feat-pill.ok   { border-color: var(--cyan); color: var(--cyan); background: rgba(0,229,255,.06); }
.feat-pill.neu  { border-color: var(--gold); color: var(--gold); background: rgba(255,214,0,.06); }

/* ── Section headings ── */
.section-head {
    font-family: var(--mono);
    font-size: .78rem;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 1.4rem 0 .6rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: .4rem;
}

/* ── Metric chips (sidebar / expander) ── */
.metric-row { display: flex; gap: .7rem; flex-wrap: wrap; margin-top: .5rem; }
.metric-chip {
    font-family: var(--mono);
    font-size: .8rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: .3rem .8rem;
    color: var(--text);
}
.metric-chip strong { color: var(--cyan); }

/* ── Model Info Container ── */
.model-info-container {
    background-color: #91989B;
    padding: 20px;
    border-radius: 12px;
    margin: 1.5rem 0;
}
.model-info-container .section-head {
    color: #234C58 !important;
    border-bottom-color: #234C58 !important;
    margin-top: 0;
}
.model-info-container .metric-chip {
    background: transparent !important;
    border-color: #234C58 !important;
    color: #234C58 !important;
}
.model-info-container .metric-chip strong {
    color: #1A3A43 !important;
}

/* ── Examples list ── */
.ex-url {
    font-family: var(--mono);
    font-size: .82rem;
    color: var(--cyan);
    cursor: pointer;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: .3rem .8rem;
    margin-bottom: .3rem;
    display: inline-block;
    text-decoration: none;
    transition: border-color .15s;
}
.ex-url:hover { border-color: var(--cyan); }

/* ── Streamlit image caption ── */
.css-1kyxreq { color: var(--muted) !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    font-family: var(--mono) !important;
    font-size: .85rem !important;
    color: var(--muted) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Load model & meta (with auto-train if missing)
# ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="🔄  Loading model …")
def load_model():
    model_path = "models/best_model.pkl"
    meta_path  = "models/model_meta.pkl"
    scaler_path= "models/scaler.pkl"

    if not (os.path.exists(model_path) and
            os.path.exists(meta_path)  and
            os.path.exists(scaler_path)):
        # Auto-train on first run
        from model_training import train
        train()

    with open(model_path,  "rb") as f: model  = pickle.load(f)
    with open(meta_path,   "rb") as f: meta   = pickle.load(f)
    with open(scaler_path, "rb") as f: scaler = pickle.load(f)
    return model, scaler, meta


model, scaler, meta = load_model()
feature_names  = meta["feature_names"]
model_name     = meta["model_name"]
model_metrics  = meta["metrics"]


# ─────────────────────────────────────────────────────────────
# Prediction helper
# ─────────────────────────────────────────────────────────────
def predict_url(url: str):
    """
    Extract features → scale → predict.
    Returns: label (str), confidence (float 0-1), feature dict
    """
    feats = extract_features(url, dns_check=False)

    # Build feature vector in the same order as training
    feat_vec = np.array([feats.get(f, 0) for f in feature_names]).reshape(1, -1)
    feat_scaled = scaler.transform(feat_vec)

    proba = model.predict_proba(feat_scaled)[0]   # [P(fake), P(legit)]
    
    legit_score = proba[1]
    is_legit = legit_score > 0.80
    
    label = "Legitimate URL" if is_legit else "Fake URL"
    confidence = legit_score if is_legit else proba[0]
    
    return label, confidence, feats, proba, feat_scaled[0]


# ─────────────────────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────────────────────
def render_result(label: str, confidence: float, feats: dict, url: str):
    is_legit = (label == "Legitimate URL")
    card_cls  = "legit" if is_legit else "fake"
    icon      = "✅" if is_legit else "❌"
    bar_color = "#00e676" if is_legit else "#ff1744"
    pct_color = "#00e676" if is_legit else "#ff1744"
    pct       = confidence * 100

    st.markdown(f"""
    <div class="result-card {card_cls}">
      <div class="result-icon">{icon}</div>
      <p class="result-label {card_cls}">{label}</p>
      <p class="result-sub">{url[:72]}{"…" if len(url)>72 else ""}</p>
      <div class="conf-wrap">
        <div class="conf-label">CONFIDENCE SCORE</div>
        <div class="conf-bar-bg">
          <div class="conf-bar-fill" style="width:{pct:.1f}%;background:{bar_color};"></div>
        </div>
        <div class="conf-pct" style="color:{pct_color};">{pct:.1f}%</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Lazy-Loading Pie Chart (Replaces Feature Pills) ──
    st.markdown('<div class="section-head">Feature Analysis Progress</div>', unsafe_allow_html=True)
    chart_placeholder = st.empty()
    status_text = st.empty()
    
    import time
    try:
        import plotly.graph_objects as go
        use_plotly = True
    except ImportError:
        use_plotly = False
        import matplotlib.pyplot as plt

    feat_items = list(feats.items())
    total_steps = max(1, len(feat_items))
        
    for i, (fname, fval) in enumerate(feat_items):
        time.sleep(0.12)  # Simulate analysis delay
        progress = ((i + 1) / total_steps) * 100
        
        status_text.markdown(f"**Analyzing component:** `{fname.replace('_', ' ')}` ...")
        
        if use_plotly:
            fig = go.Figure(data=[go.Pie(
                labels=["Processed", "Pending"],
                values=[progress, 100 - progress],
                marker_colors=["#4D0E13", "#EEE4DA"],
                hole=0.5,
                textinfo="none"
            )])
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            chart_placeholder.plotly_chart(fig, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(3, 3))
            ax.pie([progress, 100 - progress], colors=["#4D0E13", "#EEE4DA"], startangle=90)
            ax.axis('equal')
            fig.patch.set_alpha(0.0)
            chart_placeholder.pyplot(fig)
            plt.close(fig)

    # Final Result Pie Chart
    legit_pct = confidence * 100 if label == "Legitimate URL" else (1 - confidence) * 100
    fake_pct = 100 - legit_pct
    
    status_text.markdown(f"**Analysis Complete!** Final Confidence: **{confidence*100:.1f}% {label}**")
    
    if use_plotly:
        fig = go.Figure(data=[go.Pie(
            labels=["Legitimate", "Fake / Phishing"],
            values=[legit_pct, fake_pct],
            marker_colors=["#2E8B57", "#E43B44"],
            hole=0.5,
            textinfo="label+percent"
        )])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        chart_placeholder.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie([legit_pct, fake_pct], labels=["Legitimate", "Fake / Phishing"], colors=["#2E8B57", "#E43B44"], autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        fig.patch.set_alpha(0.0)
        chart_placeholder.pyplot(fig)
        plt.close(fig)


def render_model_info():
    st.markdown('<div class="model-info-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-head">Model Info</div>', unsafe_allow_html=True)
    row = '<div class="metric-row">'
    for k, v in model_metrics.items():
        row += f'<span class="metric-chip"><strong>{k}</strong>: {v:.4f}</span>'
    row += f'<span class="metric-chip"><strong>Algorithm</strong>: {model_name}</span>'
    row += "</div></div>"
    st.markdown(row, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Authentication Check
# ─────────────────────────────────────────────────────────────
if not require_login():
    st.stop()  # Stop execution if not logged in

# ─────────────────────────────────────────────────────────────
# Main UI
# ─────────────────────────────────────────────────────────────
# Banner
st.markdown("""
<div class="banner">
  <h1>PhishGuard</h1>
</div>
""", unsafe_allow_html=True)

# ── Input row ────────────────────────────────────────────────
url_input = st.text_input(
    label="",
    placeholder="https://enter-any-url-to-check.com",
    key="url_box",
    label_visibility="collapsed",
)
check_btn = st.button("🔍  Check Website", use_container_width=False)

# ── Quick examples ───────────────────────────────────────────
with st.expander("💡  Try example URLs"):
    st.markdown("""
    **✅ Legitimate**
    ```
    https://www.google.com
    https://www.github.com
    https://www.amazon.com
    ```
    **🚨 Phishing / Fake**
    ```
    http://paypa1.com-secure-login.tk/account
    http://192.168.1.1/bank-login
    http://apple-id-locked.com/verify-now
    http://secure-ebay-account.com/signin
    ```
    """)

# ── Run prediction ───────────────────────────────────────────
if check_btn:
    raw = url_input.strip()
    if not raw:
        st.warning("⚠️  Please enter a URL first.")
    else:
        with st.spinner("Analysing URL …"):
            try:
                label, confidence, feats, proba, feat_scaled_1d = predict_url(raw)
                render_result(label, confidence, feats, raw)
                
                # --- NEW REDIRECT BUTTON FEATURE ---
                if label == "Legitimate URL":
                    target_url = raw if raw.startswith(("http://", "https://")) else "https://" + raw
                    st.markdown(f"""
                        <div style="margin-top: 15px; margin-bottom: 15px; text-align: center;">
                            <p style="color: #4D0E13; font-size: 0.95rem; margin-bottom: 8px; font-weight: bold;">
                                ⚠️ Proceed only if you trust this website
                            </p>
                            <a href="{target_url}" target="_blank" style="
                                display: inline-block;
                                background-color: #29281E;
                                color: #E7D4BB;
                                padding: 12px 24px;
                                border-radius: 8px;
                                text-decoration: none;
                                font-weight: bold;
                                font-family: sans-serif;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                transition: background-color 0.3s;
                                ">
                                🌐 Open Safe Website
                            </a>
                        </div>
                    """, unsafe_allow_html=True)
                # -----------------------------------
                
                # ── Dynamic Model metrics per URL ────────────────────────────
                render_model_info()

                # ── Dynamic URL Report Charts ───────────────────────────────
                img_col1, img_col2 = st.columns(2)
                
                with img_col1:
                    st.markdown('<div class="section-head">Feature Importance (For this URL)</div>', unsafe_allow_html=True)
                    if hasattr(model, "feature_importances_"):
                        impact = model.feature_importances_ * feat_scaled_1d
                    elif hasattr(model, "coef_"):
                        impact = model.coef_[0] * feat_scaled_1d
                    else:
                        impact = feat_scaled_1d
                    # Sort features by absolute impact
                    imp_df = pd.DataFrame({"Impact": impact}, index=feature_names)
                    imp_df["Abs"] = imp_df["Impact"].abs()
                    top_imp = imp_df.sort_values(by="Abs", ascending=False).head(10)
                    st.bar_chart(top_imp["Impact"], color="#4D0E13")

                with img_col2:
                    st.markdown('<div class="section-head">Model Comparison (Probabilities)</div>', unsafe_allow_html=True)
                    prob_df = pd.DataFrame({"Probability": [proba[0], proba[1]]}, index=["Fake", "Legitimate"])
                    st.bar_chart(prob_df, color="#4D0E13")
                    
            except Exception as e:
                st.error(f"❌  Error analysing URL: {e}")

# ── Footer ───────────────────────────────────────────────────
st.markdown("""
<hr style="border:none;border-top:1px solid #1e2535;margin:2rem 0 .8rem;">
<p style="color:#3d4a60;font-size:.75rem;font-family:'Share Tech Mono',monospace;text-align:center;">
PhishGuard · Built with Python, scikit-learn & Streamlit ·
For educational / research purposes only.
</p>
""", unsafe_allow_html=True)
