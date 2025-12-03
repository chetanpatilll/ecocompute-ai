import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.carbon_scheduler import scheduler
from backend.job_queue import GPUJob, JobStatus
import uuid

# Page config
st.set_page_config(
    page_title="EcoCompute AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for branding (dark, minimal, techy)
st.markdown("""
<style>
    :root {
        --bg-main: #050816;
        --bg-elevated: rgba(15,23,42,0.96);
        --bg-soft: rgba(15,23,42,0.85);
        --accent: #6366f1;
        --accent-soft: rgba(99,102,241,0.18);
        --accent-strong: #a855f7;
        --text-primary: #e5e7eb;
        --text-muted: #9ca3af;
        --border-subtle: rgba(148,163,184,0.35);
        --shadow-soft: 0 18px 45px rgba(15,23,42,0.85);
        --radius-lg: 18px;
        --radius-md: 12px;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top, #111827 0, #020617 45%, #000000 100%);
        color: var(--text-primary);
    }

    /* Center content with comfortable width on all screens */
    .main .block-container {
        max-width: 1120px;
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(145deg, #020617 0%, #020617 40%, #111827 100%);
        border-right: 1px solid rgba(75,85,99,0.5);
    }

    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* Tagline + header */
    .app-header-title {
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .app-tagline {
        font-size: 0.9rem;
        color: var(--text-muted);
        margin-bottom: 1.5rem;
    }

    /* Metric grid */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        background: radial-gradient(circle at top left, #1f2937 0, #020617 60%);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-subtle);
        padding: 0.85rem 1rem;
        box-shadow: var(--shadow-soft);
        position: relative;
        overflow: hidden;
        transition: transform 0.18s ease-out, box-shadow 0.18s ease-out, border-color 0.18s ease-out;
        backdrop-filter: blur(14px);
    }

    .metric-card::before {
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at top left, rgba(99,102,241,0.26), transparent 55%);
        opacity: 0;
        transition: opacity 0.22s ease-out;
        pointer-events: none;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(129,140,248,0.85);
        box-shadow: 0 22px 60px rgba(17,24,39,0.95);
    }

    .metric-card:hover::before {
        opacity: 1;
    }

    .metric-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: var(--text-muted);
        margin-bottom: 0.1rem;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 650;
        color: #f9fafb;
        display: flex;
        align-items: baseline;
        gap: 0.25rem;
    }

    .metric-chip {
        font-size: 0.70rem;
        padding: 0.1rem 0.55rem;
        border-radius: 999px;
        background: var(--accent-soft);
        color: #e0e7ff;
        border: 1px solid rgba(129,140,248,0.6);
    }

    .metric-sub {
        font-size: 0.78rem;
        color: var(--text-muted);
        margin-top: 0.16rem;
    }

    /* Recommendation boxes */
    .green-box, .red-box {
        border-radius: var(--radius-lg);
        padding: 1.3rem 1.4rem;
        border-left-width: 3px;
        border-left-style: solid;
        backdrop-filter: blur(12px);
        box-shadow: var(--shadow-soft);
    }

    .green-box {
        background: linear-gradient(135deg, rgba(16,185,129,0.16), rgba(15,23,42,0.96));
        border-left-color: #22c55e;
    }

    .red-box {
        background: linear-gradient(135deg, rgba(239,68,68,0.18), rgba(15,23,42,0.96));
        border-left-color: #f97373;
    }

    /* Section titles */
    .section-title {
        font-size: 0.9rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-top: 0.4rem;
        margin-bottom: 0.6rem;
    }

    /* Plotly charts in dark mode */
    .js-plotly-plot, .plot-container {
        border-radius: var(--radius-lg) !important;
        overflow: hidden !important;
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(
    '<div class="app-header-title">🌱 EcoCompute AI</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="app-tagline">Carbon-aware compute for climate-conscious creators and live music fans.</div>',
    unsafe_allow_html=True,
)

# Sidebar: Region & Controls
with st.sidebar:
    st.header("⚙️ Configuration")
    region = st.selectbox("Select Region", 
                         ["IN", "US", "DE", "NO", "AU"],
                         help="Select your electricity grid region")
    
    refresh_rate = st.slider("Refresh Rate (seconds)", 5, 60, 15)
    
    st.divider()
    
    if st.button("🔄 Refresh Now"):
        st.rerun()
    
    st.divider()
    
    st.subheader("📝 Submit New GPU Job")
    job_name = st.text_input("Job Name", "training_job_1")
    duration = st.slider("Duration (minutes)", 5, 480, 30)
    power = st.slider("GPU Power Draw (watts)", 100, 400, 250)
    priority = st.slider("Priority (1=low, 5=high)", 1, 5, 3)
    carbon_threshold = st.slider("Carbon Intensity Threshold", 100, 800, 400)
    
    if st.button("➕ Submit Job", use_container_width=True):
        job_id = str(uuid.uuid4())[:8]
        new_job = GPUJob(
            job_id=job_id,
            name=job_name,
            duration_minutes=duration,
            power_draw_watts=power,
            priority=priority,
            carbon_intensity_threshold=carbon_threshold
        )
        scheduler.job_queue.add_job(new_job)
        st.success(f"✅ Job submitted: {job_id}")
        st.rerun()

# Main Dashboard
tabs = st.tabs(
    [
        "📊 Dashboard",
        "📋 Jobs Queue",
        "📈 Analytics",
        "🔍 Carbon Intensity",
    ]
)

# TAB 1: Dashboard
with tabs[0]:
    stats = scheduler.get_dashboard_stats()

    total_jobs = stats["total_jobs_submitted"]
    pending = stats["pending"]
    scheduled = stats["scheduled"]
    completed = stats["completed"]
    co2_kg = stats["total_emissions_kg"]

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Jobs submitted</div>
                <div class="metric-value">
                    {total_jobs}
                    <span class="metric-chip">all time</span>
                </div>
                <div class="metric-sub">All GPU jobs you&apos;ve sent to EcoCompute AI.</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">In the queue</div>
                <div class="metric-value">
                    {pending}
                    <span class="metric-chip">{scheduled} scheduled</span>
                </div>
                <div class="metric-sub">Pending jobs waiting for a greener window.</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Completed</div>
                <div class="metric-value">
                    {completed}
                </div>
                <div class="metric-sub">Jobs that finished with emissions tracked.</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">CO₂ tracked</div>
                <div class="metric-value">
                    {co2_kg:.2f}<span style="font-size:0.9rem;">kg</span>
                </div>
                <div class="metric-sub">Total emissions measured across all runs.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    
    # Grid Status & Recommendation
    grid_status = scheduler.carbon_provider.get_grid_carbon_intensity(region)
    
    col_grid1, col_grid2 = st.columns(2)
    
    with col_grid1:
        intensity = grid_status['carbonIntensity']
        greenness = grid_status['greenness']
        
        if greenness == "HIGH":
            st.markdown("""
            <div class="green-box">
                <h3>✅ Grid is CLEAN!</h3>
                <h2 style="color: green;">""" + f"{intensity:.0f} gCO2/kWh" + """</h2>
                <p><strong>Recommendation:</strong> Run GPU jobs NOW!</p>
            </div>
            """, unsafe_allow_html=True)
        elif greenness == "MEDIUM":
            st.markdown(f"""
            <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 4px solid #ffc107;">
                <h3>⏳ Grid is MODERATE</h3>
                <h2 style="color: #ff9800;">{intensity:.0f} gCO2/kWh</h2>
                <p><strong>Recommendation:</strong> Consider waiting for cleaner hours</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="red-box">
                <h3>❌ Grid is DIRTY</h3>
                <h2 style="color: red;">{intensity:.0f} gCO2/kWh</h2>
                <p><strong>Recommendation:</strong> Defer non-urgent jobs</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_grid2:
        # Real-time gauge chart
        fig = go.Figure(data=[go.Indicator(
            mode="gauge+number+delta",
            value=intensity,
            title={'text': "Carbon Intensity"},
            delta={'reference': 400},
            gauge={
                'axis': {'range': [0, 1000]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 200], 'color': "#90EE90"},  # Light green
                    {'range': [200, 400], 'color': "#FFD700"},  # Gold
                    {'range': [400, 1000], 'color': "#FF6B6B"}  # Red
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 400
                }
            }
        )])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Schedule the next batch of jobs
    col_action1, col_action2 = st.columns(2)
    
    with col_action1:
        if st.button("🎯 Schedule Pending Jobs", use_container_width=True):
            schedule_result = scheduler.schedule_pending_jobs(region)
            st.session_state.last_schedule = schedule_result
            st.success(f"Scheduled {schedule_result['scheduled_count']} jobs, deferred {schedule_result['deferred_count']}")
    
    with col_action2:
        if st.button("▶️ Run Next Scheduled Job", use_container_width=True):
            scheduled = scheduler.job_queue.get_jobs_by_status(
                JobStatus.SCHEDULED.value
            )
            if scheduled:
                next_job = scheduled[0]
                result = scheduler.run_scheduled_job(next_job.job_id)
                st.success(
                    f"Job {next_job.job_id} completed: "
                    f"{result['emissions_kg_co2']:.4f} kg CO₂ tracked"
                )
            else:
                st.warning("No scheduled jobs to run")

# TAB 2: Jobs Queue
with tabs[1]:
    st.subheader("📋 Job Queue Status")
    
    # Show jobs by status
    status_tabs = st.tabs([
        "⏳ Pending",
        "📅 Scheduled",
        "▶️ Running",
        "✅ Completed",
        "⏸️ Deferred"
    ])
    
    statuses = [
        JobStatus.PENDING.value,
        JobStatus.SCHEDULED.value,
        JobStatus.RUNNING.value,
        JobStatus.COMPLETED.value,
        JobStatus.DEFERRED.value
    ]
    
    for tab, status in zip(status_tabs, statuses):
        with tab:
            jobs = scheduler.job_queue.get_jobs_by_status(status)
            
            if jobs:
                df = pd.DataFrame([
                    {
                        'Job ID': j.job_id,
                        'Name': j.name,
                        'Duration (min)': j.duration_minutes,
                        'Power (W)': j.power_draw_watts,
                        'Priority': j.priority,
                        'Submitted': j.submitted_at[:10],
                        'Status': j.status,
                        'CO₂ Avoided (kg)': f"{j.emissions_avoided_kg:.4f}"
                    }
                    for j in jobs
                ])
                st.dataframe(df, use_container_width=True)
            else:
                st.info(f"No {status} jobs")

# TAB 3: Analytics
with tabs[2]:
    st.subheader("📈 Emissions Analytics")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        emissions_summary = scheduler.emissions_tracker.get_emissions_summary()
        
        fig = go.Figure(data=[go.Indicator(
            mode="number+delta",
            value=emissions_summary['total_emissions_kg'],
            title="Total CO₂ Emissions Tracked",
            delta={'reference': 0, 'relative': False}
        )])
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        if emissions_summary['total_jobs'] > 0:
            fig = go.Figure(data=[go.Indicator(
                mode="gauge+number",
                value=emissions_summary['avg_emissions_per_job_kg'],
                title="Avg CO₂ per Job (kg)",
                gauge={'axis': {'range': [0, 0.5]}}
            )])
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
    
    # Jobs completion trend
    st.subheader("Job Completion Trend")
    
    emissions_log = scheduler.emissions_tracker.emissions_log
    if emissions_log:
        df_emissions = pd.DataFrame(emissions_log)
        df_emissions['timestamp'] = pd.to_datetime(df_emissions['timestamp'])
        df_emissions = df_emissions.sort_values('timestamp')
        df_emissions['cumulative_co2'] = df_emissions['emissions_kg_co2'].cumsum()
        
        fig = px.line(
            df_emissions,
            x='timestamp',
            y=['emissions_kg_co2', 'cumulative_co2'],
            title="Emissions Over Time",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

# TAB 4: Carbon Intensity by Region
with tabs[3]:
    st.subheader("🌍 Multi-Region Carbon Intensity Comparison")
    
    regions = ["IN", "US", "DE", "NO", "AU"]
    comparison = scheduler.carbon_provider.get_multi_region_comparison(regions)
    
    # Create comparison dataframe
    region_data = []
    for region_code, data in comparison['regions'].items():
        region_data.append({
            'Region': region_code,
            'Carbon Intensity (gCO2/kWh)': data['carbonIntensity'],
            'Greenness': data['greenness'],
            'Recommendation': data['recommendation']
        })
    
    df_regions = pd.DataFrame(region_data)
    
    # Bar chart
    fig = px.bar(
        df_regions,
        x='Region',
        y='Carbon Intensity (gCO2/kWh)',
        color='Greenness',
        color_discrete_map={'HIGH': '#90EE90', 'MEDIUM': '#FFD700', 'LOW': '#FF6B6B'},
        title="Carbon Intensity by Region"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Table
    st.dataframe(df_regions, use_container_width=True)
    
    st.info(
        f"**Greenest Region:** {comparison['greenest_region']} "
        f"({comparison['greenest_intensity']:.0f} gCO2/kWh)"
    )

# Footer
st.divider()
st.markdown("""
---
**EcoCompute AI**  
*Reducing compute emissions, one job at a time* 🌍  
Built for [Hackathon] | [GitHub](https://github.com) | [Docs](https://greengl.docs)
""")
