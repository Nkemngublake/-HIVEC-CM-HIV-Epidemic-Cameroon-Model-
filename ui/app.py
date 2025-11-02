"""
HIVEC-CM Web Interface
Streamlit-based UI for HIV Epidemic Model Parameter Configuration and Execution
"""

import streamlit as st
import json
import os
import sys
import subprocess
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hivec_cm.scenarios.scenario_definitions import SCENARIO_REGISTRY, list_scenarios

# Page configuration
st.set_page_config(
    page_title="HIVEC-CM Model Interface",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-top: 1rem;
    }
    .info-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'simulation_results' not in st.session_state:
        st.session_state.simulation_results = None
    if 'selected_scenarios' not in st.session_state:
        st.session_state.selected_scenarios = ['S0_baseline']


def load_default_parameters():
    """Load default parameters from config file."""
    config_path = Path(__file__).parent.parent / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def save_parameters(params, filename="custom_parameters.json"):
    """Save parameters to file."""
    config_dir = Path(__file__).parent.parent / "config"
    config_dir.mkdir(exist_ok=True)
    
    filepath = config_dir / filename
    with open(filepath, 'w') as f:
        json.dump(params, f, indent=2)
    
    return filepath


def run_simulation(scenarios, population, years, start_year, output_dir, config_file):
    """Run the simulation with specified parameters."""
    script_path = Path(__file__).parent.parent / "scripts" / "run_all_scenarios.py"
    
    cmd = [
        sys.executable,
        str(script_path),
        "--scenarios", *scenarios,
        "--population", str(population),
        "--years", str(years),
        "--start-year", str(start_year),
        "--output-dir", str(output_dir),
        "--config", str(config_file)
    ]
    
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def main():
    """Main application."""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🦠 HIVEC-CM: HIV Epidemic Cameroon Model</h1>', unsafe_allow_html=True)
    st.markdown("### Interactive Parameter Configuration & Simulation Interface")
    
    # Sidebar - Main Navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=HIVEC-CM", use_column_width=True)
        
        page = st.radio(
            "Navigation",
            [
                "🎛️ Configure & Run", 
                "📊 View Results", 
                "📈 Compare Scenarios",
                "📖 Documentation", 
                "⚙️ Advanced Settings"
            ],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### Quick Info")
        st.info("**Model Version:** 7.0 (Time-Varying)\n\n**Calibration:** MAE=1.73%\n\n**Status:** Production Ready")
    
    # Main content based on page selection
    if page == "🎛️ Configure & Run":
        configure_and_run_page()
    elif page == "📊 View Results":
        view_results_page()
    elif page == "📈 Compare Scenarios":
        compare_scenarios_page()
    elif page == "📖 Documentation":
        documentation_page()
    elif page == "⚙️ Advanced Settings":
        advanced_settings_page()


def configure_and_run_page():
    """Main configuration and run page."""
    st.markdown('<h2 class="sub-header">Simulation Configuration</h2>', unsafe_allow_html=True)
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Scenarios", "⏱️ Time & Population", "🔧 Model Parameters", "📁 Output Settings"])
    
    # Tab 1: Scenario Selection
    with tab1:
        st.markdown("### Select Policy Scenarios to Simulate")
        
        scenarios_list = list_scenarios()
        
        # Display scenarios with descriptions
        col1, col2 = st.columns(2)
        
        selected_scenarios = []
        
        for i, scenario in enumerate(scenarios_list):
            with col1 if i % 2 == 0 else col2:
                with st.expander(f"**{scenario['name']}** ({scenario['id']})", expanded=False):
                    st.write(scenario['description'])
                    
                    if st.checkbox(f"Select {scenario['id']}", key=f"scenario_{scenario['id']}",
                                 value=scenario['id'] == 'S0_baseline'):
                        selected_scenarios.append(scenario['id'])
        
        st.session_state.selected_scenarios = selected_scenarios
        
        if selected_scenarios:
            st.success(f"✅ {len(selected_scenarios)} scenario(s) selected: {', '.join(selected_scenarios)}")
        else:
            st.warning("⚠️ Please select at least one scenario to run.")
        
        # Quick select buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Select All", use_container_width=True):
                st.session_state.selected_scenarios = [s['id'] for s in scenarios_list]
                st.rerun()
        with col2:
            if st.button("Select Funding Scenarios", use_container_width=True):
                st.session_state.selected_scenarios = ['S0_baseline', 'S1a_optimistic_funding', 'S1b_pessimistic_funding']
                st.rerun()
        with col3:
            if st.button("Clear All", use_container_width=True):
                st.session_state.selected_scenarios = []
                st.rerun()
    
    # Tab 2: Time and Population Settings
    with tab2:
        st.markdown("### Time Period and Population Size")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_year = st.number_input(
                "Start Year",
                min_value=1980,
                max_value=2020,
                value=1985,
                step=1,
                help="Year to begin simulation (historical period starts)"
            )
            
            end_year = st.number_input(
                "End Year",
                min_value=start_year + 10,
                max_value=2100,
                value=2070,
                step=1,
                help="Year to end simulation (projection period)"
            )
            
            years = end_year - start_year
            st.info(f"**Simulation Duration:** {years} years")
        
        with col2:
            population = st.number_input(
                "Population Size (agents)",
                min_value=1000,
                max_value=1000000,
                value=100000,
                step=5000,
                help="Number of agents in the model. Cameroon ~11.9M people."
            )
            
            scaling_ratio = 11900000 / population
            st.info(f"**Scaling Ratio:** 1:{scaling_ratio:.0f}\n\n(1 agent = {scaling_ratio:.0f} real people)")
            
            dt = st.select_slider(
                "Time Step (years)",
                options=[0.05, 0.1, 0.25, 0.5, 1.0],
                value=0.1,
                help="Smaller steps = more accurate but slower"
            )
            
            total_steps = int(years / dt)
            st.metric("Total Simulation Steps", f"{total_steps:,}")
        
        # Estimation
        st.markdown("---")
        st.markdown("### Execution Time Estimation")
        
        estimated_time_per_scenario = (population / 10000) * (years / 35) * 3  # rough estimate in minutes
        total_estimated_time = estimated_time_per_scenario * len(st.session_state.selected_scenarios)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Per Scenario", f"{estimated_time_per_scenario:.1f} min")
        col2.metric("Total Time", f"{total_estimated_time:.1f} min ({total_estimated_time/60:.1f} hrs)")
        col3.metric("Agent-Years", f"{(population * years / 1000000):.1f}M")
    
    # Tab 3: Model Parameters
    with tab3:
        st.markdown("### Core Model Parameters")
        
        params = load_default_parameters()
        
        # Transmission parameters
        st.markdown("#### 🦠 Transmission Parameters")
        col1, col2 = st.columns(2)
        
        with col1:
            base_transmission = st.slider(
                "Base Transmission Rate",
                min_value=0.001,
                max_value=0.010,
                value=float(params.get('base_transmission_rate', 0.0025)),
                step=0.0001,
                format="%.4f",
                help="Baseline probability of transmission per contact"
            )
            
            initial_prevalence = st.slider(
                "Initial HIV Prevalence (%)",
                min_value=0.0,
                max_value=1.0,
                value=float(params.get('initial_hiv_prevalence', 0.0002)) * 100,
                step=0.01,
                format="%.3f",
                help="Starting HIV prevalence at simulation start"
            ) / 100
        
        with col2:
            mean_contacts = st.slider(
                "Mean Contacts per Year",
                min_value=0.5,
                max_value=10.0,
                value=float(params.get('mean_contacts_per_year', 2.5)),
                step=0.1,
                help="Average number of sexual contacts per person per year"
            )
        
        # Time-varying transmission
        st.markdown("#### 📈 Time-Varying Transmission Multipliers")
        st.info("These multipliers adjust transmission rates by epidemic phase (calibrated to UNAIDS data)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            emergence_mult = st.slider(
                "Emergence (1985-1990)",
                min_value=0.1,
                max_value=2.0,
                value=float(params.get('emergence_phase_multiplier', 0.80)),
                step=0.1,
                help="Low transmission during emergence phase"
            )
        
        with col2:
            growth_mult = st.slider(
                "Growth (1990-2007)",
                min_value=1.0,
                max_value=10.0,
                value=float(params.get('growth_phase_multiplier', 6.0)),
                step=0.5,
                help="High transmission during epidemic growth"
            )
        
        with col3:
            decline_mult = st.slider(
                "Decline (2007+)",
                min_value=1.0,
                max_value=8.0,
                value=float(params.get('decline_phase_multiplier', 4.0)),
                step=0.5,
                help="Elevated baseline to counter ART suppression"
            )
        
        # Treatment parameters
        st.markdown("#### 💊 Treatment Parameters")
        col1, col2 = st.columns(2)
        
        with col1:
            art_efficacy = st.slider(
                "ART Viral Suppression Efficacy (%)",
                min_value=70,
                max_value=99,
                value=int(params.get('art_viral_suppression_efficacy', 92)),
                step=1,
                help="Percentage reduction in viral load when on ART with good adherence"
            )
        
        with col2:
            art_mortality_reduction = st.slider(
                "ART Mortality Reduction (%)",
                min_value=50,
                max_value=95,
                value=int(params.get('art_mortality_reduction', 85)),
                step=5,
                help="Percentage reduction in HIV-related mortality on ART"
            )
        
        # Save parameters button
        if st.button("💾 Save Custom Parameters", use_container_width=True):
            custom_params = params.copy()
            custom_params.update({
                'base_transmission_rate': base_transmission,
                'initial_hiv_prevalence': initial_prevalence,
                'mean_contacts_per_year': mean_contacts,
                'emergence_phase_multiplier': emergence_mult,
                'growth_phase_multiplier': growth_mult,
                'decline_phase_multiplier': decline_mult,
                'art_viral_suppression_efficacy': art_efficacy / 100,
                'art_mortality_reduction': art_mortality_reduction / 100
            })
            
            filepath = save_parameters(custom_params)
            st.success(f"✅ Parameters saved to: {filepath}")
    
    # Tab 4: Output Settings
    with tab4:
        st.markdown("### Output Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            output_name = st.text_input(
                "Output Directory Name",
                value=f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                help="Name for the results directory"
            )
            
            base_output = st.text_input(
                "Base Results Path",
                value="results",
                help="Base directory for all results"
            )
            
            output_dir = Path(base_output) / output_name
            st.info(f"**Full Output Path:**\n`{output_dir}`")
        
        with col2:
            save_detailed = st.checkbox(
                "Save Detailed Results",
                value=True,
                help="Save age-sex-region stratified data (larger files)"
            )
            
            save_plots = st.checkbox(
                "Generate Plots Automatically",
                value=True,
                help="Create visualization plots after each scenario"
            )
            
            compress_results = st.checkbox(
                "Compress Results",
                value=False,
                help="Compress CSV files to save disk space"
            )
    
    # Run Simulation Section
    st.markdown("---")
    st.markdown('<h2 class="sub-header">Execute Simulation</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if not st.session_state.selected_scenarios:
            st.error("❌ Please select at least one scenario before running.")
        else:
            st.success(f"✅ Ready to run {len(st.session_state.selected_scenarios)} scenario(s)")
            st.write(f"**Selected:** {', '.join(st.session_state.selected_scenarios)}")
    
    with col2:
        if st.button("🚀 START SIMULATION", type="primary", use_container_width=True, 
                    disabled=len(st.session_state.selected_scenarios) == 0):
            
            # Save current parameters
            custom_params = params.copy()
            custom_params.update({
                'base_transmission_rate': base_transmission,
                'initial_hiv_prevalence': initial_prevalence,
                'initial_population': population,
                'mean_contacts_per_year': mean_contacts,
                'emergence_phase_multiplier': emergence_mult,
                'growth_phase_multiplier': growth_mult,
                'decline_phase_multiplier': decline_mult
            })
            config_file = save_parameters(custom_params, f"run_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # Start simulation
            st.session_state.simulation_running = True
            st.session_state.process = run_simulation(
                st.session_state.selected_scenarios,
                population,
                years,
                start_year,
                output_dir,
                config_file
            )
            
            st.success("🚀 Simulation started!")
            st.rerun()
    
    with col3:
        if st.button("⏹️ STOP", use_container_width=True, disabled=not st.session_state.simulation_running):
            if hasattr(st.session_state, 'process'):
                st.session_state.process.terminate()
                st.session_state.simulation_running = False
                st.warning("⏹️ Simulation stopped.")
                st.rerun()
    
    # Show progress if running
    if st.session_state.simulation_running:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### 🔄 Live Simulation Monitor")
        
        # Check for progress file
        progress_file = output_dir / ".progress.json"
        
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    progress_data = json.load(f)
                
                # Overall Progress
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.progress(progress_data.get('overall_progress', 0) / 100)
                with col2:
                    st.metric("Overall", f"{progress_data.get('overall_progress', 0):.1f}%")
                
                # Current Scenario Info
                st.markdown(f"**Current Scenario:** `{progress_data.get('scenario', 'Unknown')}`  "
                          f"(#{progress_data.get('scenario_num', 0)}/{progress_data.get('total_scenarios', 0)})")
                
                # Year Progress
                current_year = progress_data.get('current_year', 0)
                st.markdown(f"**Simulation Year:** {current_year:.1f}")
                year_prog = progress_data.get('year_progress', 0) / 100
                st.progress(year_prog)
                
                # Live Agent Statistics
                st.markdown("#### 📊 Live Agent Statistics")
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric(
                        "👥 Agents Alive",
                        f"{progress_data.get('agents_alive', 0):,}",
                        help="Total agents currently in simulation"
                    )
                
                with metric_col2:
                    hiv_pos = progress_data.get('agents_hiv_positive', 0)
                    prevalence = progress_data.get('prevalence', 0)
                    st.metric(
                        "🦠 HIV+ Agents",
                        f"{hiv_pos:,}",
                        delta=f"{prevalence:.2f}% prevalence",
                        delta_color="inverse"
                    )
                
                with metric_col3:
                    on_art = progress_data.get('agents_on_art', 0)
                    art_cov = progress_data.get('art_coverage', 0)
                    st.metric(
                        "💊 On ART",
                        f"{on_art:,}",
                        delta=f"{art_cov:.1f}% coverage"
                    )
                
                with metric_col4:
                    new_inf = progress_data.get('new_infections_this_year', 0)
                    st.metric(
                        "🔴 New Infections",
                        f"{new_inf:,}",
                        help="New infections this simulation year"
                    )
                
                # Live Plot - Prevalence Evolution
                live_data_file = output_dir / ".live_data.json"
                if live_data_file.exists():
                    try:
                        live_data = []
                        with open(live_data_file, 'r') as f:
                            for line in f:
                                try:
                                    live_data.append(json.loads(line.strip()))
                                except:
                                    continue
                        
                        if live_data:
                            df_live = pd.DataFrame(live_data)
                            if not df_live.empty and 'current_year' in df_live.columns:
                                st.markdown("#### 📈 Live Prevalence Evolution")
                                
                                fig = px.line(
                                    df_live,
                                    x='current_year',
                                    y='prevalence',
                                    color='scenario',
                                    title='HIV Prevalence Over Time (Live)',
                                    labels={'current_year': 'Year',
                                            'prevalence': 'HIV Prevalence (%)'}
                                )
                                fig.update_layout(height=300)
                                st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not load live plot data: {e}")
            
            except Exception as e:
                st.warning(f"Could not read progress: {e}")
        else:
            # Fallback to basic progress tracking
            if output_dir.exists():
                completed = len([d for d in output_dir.iterdir()
                               if d.is_dir() and (d / "simulation_results.csv").exists()])
                total = len(st.session_state.selected_scenarios)
                progress = completed / total if total > 0 else 0
                
                st.progress(progress)
                st.text(f"Completed: {completed}/{total} scenarios")
                
                if completed == total:
                    st.session_state.simulation_running = False
                    st.success("✅ All scenarios completed!")
                    st.balloons()
            else:
                st.info("⏳ Initializing simulation...")
        
        # Auto-refresh
        time.sleep(2)
        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


def view_results_page():
    """Page to view and analyze results."""
    st.markdown('<h2 class="sub-header">Results Viewer</h2>', unsafe_allow_html=True)
    
    results_base = Path(__file__).parent.parent / "results"
    
    if not results_base.exists():
        st.warning("No results directory found. Run a simulation first.")
        return
    
    # List available result directories
    result_dirs = [d for d in results_base.iterdir() if d.is_dir()]
    
    if not result_dirs:
        st.info("No simulation results found yet. Run a simulation to generate results.")
        return
    
    # Select result directory
    selected_dir = st.selectbox(
        "Select Results Directory",
        options=result_dirs,
        format_func=lambda x: x.name
    )
    
    if selected_dir:
        # Display summary
        summary_file = selected_dir / "execution_summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Scenarios", summary.get('total_scenarios', 0))
            col2.metric("Successful", summary.get('successful', 0))
            col3.metric("Failed", summary.get('failed', 0))
            col4.metric("Execution Time", f"{summary.get('total_execution_time_seconds', 0)/60:.1f} min")
        
        # List scenarios
        scenario_dirs = [d for d in selected_dir.iterdir() if d.is_dir()]
        
        if scenario_dirs:
            st.markdown("### Available Scenarios")
            
            selected_scenario = st.selectbox(
                "Select Scenario to View",
                options=scenario_dirs,
                format_func=lambda x: x.name
            )
            
            if selected_scenario:
                # Create tabs for different views
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 Overview", 
                    "👥 Age-Sex Analysis", 
                    "🗺️ Regional Analysis",
                    "💾 Data Downloads"
                ])
                
                # Tab 1: Overview (existing functionality)
                with tab1:
                    # Load results
                    results_file = selected_scenario / "simulation_results.csv"
                    if results_file.exists():
                        df = pd.read_csv(results_file)
                        
                        # Display key metrics
                        st.markdown("### Key Indicators")
                        final_row = df.iloc[-1]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Final Prevalence", f"{final_row['true_hiv_prevalence']*100:.2f}%")
                        col2.metric("ART Coverage", f"{final_row['true_art_coverage']*100:.1f}%")
                        col3.metric("Population", f"{final_row['total_population']:,.0f}")
                        col4.metric("PLHIV", f"{final_row['true_hiv_positive']:,.0f}")
                        
                        # Plot prevalence trajectory
                        st.markdown("### HIV Prevalence Trajectory")
                        fig = px.line(df, x='year', y='true_hiv_prevalence',
                                    title='HIV Prevalence Over Time',
                                    labels={'true_hiv_prevalence': 'HIV Prevalence (%)',
                                            'year': 'Year'})
                        fig.update_traces(line_color='#1f77b4', line_width=3)
                        fig.update_yaxes(tickformat='.1%')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Treatment cascade
                        st.markdown("### Treatment Cascade Progress")
                        fig2 = go.Figure()
                        fig2.add_trace(go.Scatter(x=df['year'], y=df['true_hiv_positive'],
                                                 mode='lines', name='PLHIV',
                                                 line=dict(color='red', width=2)))
                        fig2.add_trace(go.Scatter(x=df['year'], y=df['diagnosed'],
                                                 mode='lines', name='Diagnosed',
                                                 line=dict(color='orange', width=2)))
                        fig2.add_trace(go.Scatter(x=df['year'], y=df['true_on_art'],
                                                 mode='lines', name='On ART',
                                                 line=dict(color='green', width=2)))
                        fig2.update_layout(title='Treatment Cascade Over Time',
                                         xaxis_title='Year',
                                         yaxis_title='Number of People')
                        st.plotly_chart(fig2, use_container_width=True)
                
                # Tab 2: Age-Sex Analysis
                with tab2:
                    detailed_csv = selected_scenario / "detailed_age_sex_results.csv"
                    if detailed_csv.exists():
                        st.markdown("### Age-Sex Stratified Analysis")
                        
                        df_detailed = pd.read_csv(detailed_csv)
                        
                        # Filter for prevalence data only (not regional)
                        age_sex_data = df_detailed[df_detailed['type'] == 'prevalence'].copy()
                        
                        if len(age_sex_data) > 0:
                            # Year selector
                            years_available = sorted(age_sex_data['year'].unique())
                            selected_years = st.multiselect(
                                "Select Years to Display",
                                options=years_available,
                                default=[years_available[0], years_available[-1]]
                            )
                            
                            if selected_years:
                                # Prevalence by Age and Sex
                                st.markdown("#### HIV Prevalence by Age Group and Sex")
                                
                                for year in selected_years:
                                    year_data = age_sex_data[age_sex_data['year'] == year]
                                    
                                    # Create pivot table
                                    pivot = year_data.pivot_table(
                                        values='prevalence_pct',
                                        index='age_group',
                                        columns='sex',
                                        aggfunc='mean'
                                    )
                                    
                                    # Bar chart
                                    fig = go.Figure()
                                    if 'M' in pivot.columns:
                                        fig.add_trace(go.Bar(
                                            x=pivot.index,
                                            y=pivot['M'],
                                            name='Male',
                                            marker_color='steelblue'
                                        ))
                                    if 'F' in pivot.columns:
                                        fig.add_trace(go.Bar(
                                            x=pivot.index,
                                            y=pivot['F'],
                                            name='Female',
                                            marker_color='salmon'
                                        ))
                                    
                                    fig.update_layout(
                                        title=f'HIV Prevalence by Age and Sex ({year})',
                                        xaxis_title='Age Group',
                                        yaxis_title='HIV Prevalence (%)',
                                        barmode='group',
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                # Time series by age group
                                st.markdown("#### Prevalence Trends by Age Group")
                                
                                age_groups = sorted(age_sex_data['age_group'].unique())
                                selected_ages = st.multiselect(
                                    "Select Age Groups",
                                    options=age_groups,
                                    default=age_groups[:3] if len(age_groups) >= 3 else age_groups
                                )
                                
                                if selected_ages:
                                    fig = go.Figure()
                                    for age in selected_ages:
                                        age_data = age_sex_data[age_sex_data['age_group'] == age]
                                        by_year = age_data.groupby('year')['prevalence_pct'].mean()
                                        fig.add_trace(go.Scatter(
                                            x=by_year.index,
                                            y=by_year.values,
                                            mode='lines',
                                            name=age,
                                            line=dict(width=2)
                                        ))
                                    
                                    fig.update_layout(
                                        title='HIV Prevalence Trends by Age Group',
                                        xaxis_title='Year',
                                        yaxis_title='HIV Prevalence (%)',
                                        height=500
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No age-sex prevalence data available.")
                    else:
                        st.warning("Detailed age-sex results not available for this scenario.")
                        st.info("� This data is available in newer simulations (e.g., Saint_Seya_Simulation_Detailed)")
                
                # Tab 3: Regional Analysis
                with tab3:
                    detailed_csv = selected_scenario / "detailed_age_sex_results.csv"
                    if detailed_csv.exists():
                        st.markdown("### Regional Stratified Analysis")
                        
                        df_detailed = pd.read_csv(detailed_csv)
                        
                        # Filter for regional data
                        regional_data = df_detailed[df_detailed['type'] == 'regional_prevalence'].copy()
                        
                        if len(regional_data) > 0:
                            # Year selector
                            years_available = sorted(regional_data['year'].unique())
                            selected_year = st.select_slider(
                                "Select Year",
                                options=years_available,
                                value=years_available[-1]
                            )
                            
                            year_data = regional_data[regional_data['year'] == selected_year]
                            
                            # Regional prevalence comparison
                            st.markdown(f"#### HIV Prevalence by Region ({selected_year})")
                            
                            regional_summary = year_data.groupby('region')['prevalence_pct'].mean().sort_values(ascending=False)
                            
                            fig = go.Figure(go.Bar(
                                x=regional_summary.values,
                                y=regional_summary.index,
                                orientation='h',
                                marker_color='teal'
                            ))
                            
                            fig.update_layout(
                                title=f'HIV Prevalence by Region ({selected_year})',
                                xaxis_title='HIV Prevalence (%)',
                                yaxis_title='Region',
                                height=500
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Regional trends over time
                            st.markdown("#### Regional Trends Over Time")
                            
                            regions = sorted(regional_data['region'].dropna().unique())
                            selected_regions = st.multiselect(
                                "Select Regions to Compare",
                                options=regions,
                                default=regions[:5] if len(regions) >= 5 else regions
                            )
                            
                            if selected_regions:
                                fig = go.Figure()
                                for region in selected_regions:
                                    region_data = regional_data[regional_data['region'] == region]
                                    by_year = region_data.groupby('year')['prevalence_pct'].mean()
                                    fig.add_trace(go.Scatter(
                                        x=by_year.index,
                                        y=by_year.values,
                                        mode='lines',
                                        name=region,
                                        line=dict(width=2)
                                    ))
                                
                                fig.update_layout(
                                    title='HIV Prevalence Trends by Region',
                                    xaxis_title='Year',
                                    yaxis_title='HIV Prevalence (%)',
                                    height=500
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No regional prevalence data available.")
                    else:
                        st.warning("Detailed regional results not available for this scenario.")
                        st.info("💡 This data is available in newer simulations (e.g., Saint_Seya_Simulation_Detailed)")
                
                # Tab 4: Downloads
                with tab4:
                    st.markdown("### Download Data Files")
                    
                    # Basic results
                    results_file = selected_scenario / "simulation_results.csv"
                    if results_file.exists():
                        with open(results_file, 'rb') as f:
                            st.download_button(
                                label="📥 Download Aggregate Results (CSV)",
                                data=f.read(),
                                file_name=f"{selected_scenario.name}_results.csv",
                                mime="text/csv"
                            )
                    
                    # Detailed age-sex results
                    detailed_csv = selected_scenario / "detailed_age_sex_results.csv"
                    if detailed_csv.exists():
                        with open(detailed_csv, 'rb') as f:
                            st.download_button(
                                label="📥 Download Detailed Age-Sex Results (CSV)",
                                data=f.read(),
                                file_name=f"{selected_scenario.name}_detailed_age_sex.csv",
                                mime="text/csv"
                            )
                    
                    # Detailed JSON results
                    detailed_json = selected_scenario / "detailed_results.json"
                    if detailed_json.exists():
                        with open(detailed_json, 'rb') as f:
                            st.download_button(
                                label="📥 Download Complete Detailed Results (JSON)",
                                data=f.read(),
                                file_name=f"{selected_scenario.name}_detailed_results.json",
                                mime="application/json"
                            )
                        
                        # Show JSON structure preview
                        with st.expander("📋 View Detailed Results Structure"):
                            with open(detailed_json, 'r') as f:
                                detailed_data = json.load(f)
                                
                            sample_year = list(detailed_data.keys())[0]
                            data_types = list(detailed_data[sample_year].keys())
                            
                            st.write(f"**Years Available:** {len(detailed_data)} years")
                            st.write(f"**Data Dimensions per Year:** {len(data_types)}")
                            st.write("**Available Data Types:**")
                            
                            for i, dtype in enumerate(data_types, 1):
                                st.write(f"  {i}. `{dtype}`")
                    
                    # Metadata
                    metadata_file = selected_scenario / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'rb') as f:
                            st.download_button(
                                label="📥 Download Scenario Metadata (JSON)",
                                data=f.read(),
                                file_name=f"{selected_scenario.name}_metadata.json",
                                mime="application/json"
                            )


def compare_scenarios_page():
    """Page to compare multiple scenarios side-by-side."""
    st.markdown('<h2 class="sub-header">Compare Scenarios</h2>', unsafe_allow_html=True)
    
    results_base = Path(__file__).parent.parent / "results"
    
    if not results_base.exists():
        st.warning("No results directory found. Run a simulation first.")
        return
    
    # List available result directories
    result_dirs = [d for d in results_base.iterdir() if d.is_dir()]
    
    if not result_dirs:
        st.info("No simulation results found yet. Run a simulation to generate results.")
        return
    
    # Select result directory
    st.markdown("### Select Results Set")
    selected_dir = st.selectbox(
        "Results Directory",
        options=result_dirs,
        format_func=lambda x: x.name,
        key="compare_dir"
    )
    
    if selected_dir:
        # List scenarios
        scenario_dirs = [d for d in selected_dir.iterdir() if d.is_dir()]
        
        if len(scenario_dirs) < 2:
            st.warning("Need at least 2 scenarios to compare. Run more scenarios first.")
            return
        
        st.markdown("### Select Scenarios to Compare")
        
        # Multi-select scenarios
        selected_scenarios = st.multiselect(
            "Choose scenarios (2-9 recommended)",
            options=scenario_dirs,
            default=scenario_dirs[:min(3, len(scenario_dirs))],
            format_func=lambda x: x.name
        )
        
        if len(selected_scenarios) >= 2:
            # Create comparison tabs
            tab1, tab2, tab3 = st.tabs([
                "📊 Overview Comparison",
                "👥 Age-Sex Comparison",
                "🗺️ Regional Comparison"
            ])
            
            # Tab 1: Overview Comparison
            with tab1:
                st.markdown("### Final Year Outcomes Comparison")
                
                # Collect data from all scenarios
                comparison_data = []
                for scenario_path in selected_scenarios:
                    results_file = scenario_path / "simulation_results.csv"
                    if results_file.exists():
                        df = pd.read_csv(results_file)
                        final = df.iloc[-1]
                        
                        comparison_data.append({
                            'Scenario': scenario_path.name,
                            'Prevalence (%)': final['true_hiv_prevalence'] * 100,
                            'PLHIV': final['true_hiv_positive'],
                            'ART Coverage (%)': final['true_art_coverage'] * 100,
                            'Population': final['total_population'],
                            'Deaths (HIV)': df['deaths_hiv'].sum(),
                            'New Infections': final['true_new_infections']
                        })
                
                if comparison_data:
                    comp_df = pd.DataFrame(comparison_data)
                    
                    # Display table
                    st.dataframe(comp_df, use_container_width=True)
                    
                    # Prevalence comparison
                    st.markdown("#### HIV Prevalence Comparison")
                    fig1 = go.Figure()
                    fig1.add_trace(go.Bar(
                        x=comp_df['Scenario'],
                        y=comp_df['Prevalence (%)'],
                        marker_color='steelblue'
                    ))
                    fig1.update_layout(
                        title='Final HIV Prevalence by Scenario',
                        xaxis_title='Scenario',
                        yaxis_title='HIV Prevalence (%)',
                        height=400
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    # ART Coverage comparison
                    st.markdown("#### ART Coverage Comparison")
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(
                        x=comp_df['Scenario'],
                        y=comp_df['ART Coverage (%)'],
                        marker_color='green'
                    ))
                    fig2.update_layout(
                        title='Final ART Coverage by Scenario',
                        xaxis_title='Scenario',
                        yaxis_title='ART Coverage (%)',
                        height=400
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    # Time series comparison
                    st.markdown("#### Prevalence Trends Over Time")
                    fig3 = go.Figure()
                    
                    for scenario_path in selected_scenarios:
                        results_file = scenario_path / "simulation_results.csv"
                        if results_file.exists():
                            df = pd.read_csv(results_file)
                            fig3.add_trace(go.Scatter(
                                x=df['year'],
                                y=df['true_hiv_prevalence'] * 100,
                                mode='lines',
                                name=scenario_path.name,
                                line=dict(width=2)
                            ))
                    
                    fig3.update_layout(
                        title='HIV Prevalence Trends Comparison',
                        xaxis_title='Year',
                        yaxis_title='HIV Prevalence (%)',
                        height=500
                    )
                    st.plotly_chart(fig3, use_container_width=True)
            
            # Tab 2: Age-Sex Comparison
            with tab2:
                st.markdown("### Age-Sex Stratified Comparison")
                
                # Check if detailed data exists
                has_detailed = all(
                    (s / "detailed_age_sex_results.csv").exists() 
                    for s in selected_scenarios
                )
                
                if has_detailed:
                    # Year selector
                    sample_csv = selected_scenarios[0] / "detailed_age_sex_results.csv"
                    sample_df = pd.read_csv(sample_csv)
                    years_available = sorted(sample_df['year'].unique())
                    
                    selected_year = st.select_slider(
                        "Select Year for Comparison",
                        options=years_available,
                        value=years_available[-1]
                    )
                    
                    # Compare prevalence by age-sex
                    st.markdown(f"#### HIV Prevalence by Age-Sex ({selected_year})")
                    
                    fig = go.Figure()
                    
                    for scenario_path in selected_scenarios:
                        detailed_csv = scenario_path / "detailed_age_sex_results.csv"
                        df_det = pd.read_csv(detailed_csv)
                        
                        # Filter for selected year and type
                        year_data = df_det[
                            (df_det['year'] == selected_year) & 
                            (df_det['type'] == 'prevalence')
                        ]
                        
                        if len(year_data) > 0:
                            # Average across sexes for simplicity
                            by_age = year_data.groupby('age_group')['prevalence_pct'].mean()
                            
                            fig.add_trace(go.Scatter(
                                x=by_age.index,
                                y=by_age.values,
                                mode='lines+markers',
                                name=scenario_path.name,
                                line=dict(width=2)
                            ))
                    
                    fig.update_layout(
                        title=f'HIV Prevalence by Age Group ({selected_year})',
                        xaxis_title='Age Group',
                        yaxis_title='HIV Prevalence (%)',
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Gender comparison
                    st.markdown(f"#### Female vs Male Prevalence ({selected_year})")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_f = go.Figure()
                        for scenario_path in selected_scenarios:
                            detailed_csv = scenario_path / "detailed_age_sex_results.csv"
                            df_det = pd.read_csv(detailed_csv)
                            year_data = df_det[
                                (df_det['year'] == selected_year) & 
                                (df_det['type'] == 'prevalence') &
                                (df_det['sex'] == 'F')
                            ]
                            if len(year_data) > 0:
                                by_age = year_data.groupby('age_group')['prevalence_pct'].mean()
                                fig_f.add_trace(go.Bar(
                                    x=by_age.index,
                                    y=by_age.values,
                                    name=scenario_path.name
                                ))
                        
                        fig_f.update_layout(
                            title='Female Prevalence',
                            xaxis_title='Age Group',
                            yaxis_title='Prevalence (%)',
                            height=400,
                            showlegend=False
                        )
                        st.plotly_chart(fig_f, use_container_width=True)
                    
                    with col2:
                        fig_m = go.Figure()
                        for scenario_path in selected_scenarios:
                            detailed_csv = scenario_path / "detailed_age_sex_results.csv"
                            df_det = pd.read_csv(detailed_csv)
                            year_data = df_det[
                                (df_det['year'] == selected_year) & 
                                (df_det['type'] == 'prevalence') &
                                (df_det['sex'] == 'M')
                            ]
                            if len(year_data) > 0:
                                by_age = year_data.groupby('age_group')['prevalence_pct'].mean()
                                fig_m.add_trace(go.Bar(
                                    x=by_age.index,
                                    y=by_age.values,
                                    name=scenario_path.name
                                ))
                        
                        fig_m.update_layout(
                            title='Male Prevalence',
                            xaxis_title='Age Group',
                            yaxis_title='Prevalence (%)',
                            height=400
                        )
                        st.plotly_chart(fig_m, use_container_width=True)
                    
                else:
                    st.warning("Detailed age-sex data not available for selected scenarios.")
                    st.info("💡 Run simulations with detailed data collection (e.g., Saint_Seya_Simulation_Detailed)")
            
            # Tab 3: Regional Comparison
            with tab3:
                st.markdown("### Regional Stratified Comparison")
                
                # Check if detailed data exists
                has_detailed = all(
                    (s / "detailed_age_sex_results.csv").exists() 
                    for s in selected_scenarios
                )
                
                if has_detailed:
                    # Year selector
                    sample_csv = selected_scenarios[0] / "detailed_age_sex_results.csv"
                    sample_df = pd.read_csv(sample_csv)
                    years_available = sorted(sample_df['year'].unique())
                    
                    selected_year = st.select_slider(
                        "Select Year for Regional Comparison",
                        options=years_available,
                        value=years_available[-1],
                        key="regional_year"
                    )
                    
                    st.markdown(f"#### Regional HIV Prevalence Comparison ({selected_year})")
                    
                    # Collect regional data
                    regional_comparison = []
                    
                    for scenario_path in selected_scenarios:
                        detailed_csv = scenario_path / "detailed_age_sex_results.csv"
                        df_det = pd.read_csv(detailed_csv)
                        
                        regional_data = df_det[
                            (df_det['year'] == selected_year) & 
                            (df_det['type'] == 'regional_prevalence')
                        ]
                        
                        if len(regional_data) > 0:
                            by_region = regional_data.groupby('region')['prevalence_pct'].mean()
                            
                            for region, prev in by_region.items():
                                regional_comparison.append({
                                    'Scenario': scenario_path.name,
                                    'Region': region,
                                    'Prevalence (%)': prev
                                })
                    
                    if regional_comparison:
                        reg_df = pd.DataFrame(regional_comparison)
                        
                        # Heatmap comparison
                        pivot = reg_df.pivot(
                            index='Region',
                            columns='Scenario',
                            values='Prevalence (%)'
                        )
                        
                        fig = go.Figure(data=go.Heatmap(
                            z=pivot.values,
                            x=pivot.columns,
                            y=pivot.index,
                            colorscale='YlOrRd',
                            text=pivot.values,
                            texttemplate='%{text:.2f}',
                            textfont={"size": 10},
                            colorbar=dict(title="Prevalence (%)")
                        ))
                        
                        fig.update_layout(
                            title=f'Regional HIV Prevalence Heatmap ({selected_year})',
                            xaxis_title='Scenario',
                            yaxis_title='Region',
                            height=600
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Bar chart comparison for selected region
                        st.markdown("#### Compare Specific Region Across Scenarios")
                        
                        regions = sorted(reg_df['Region'].unique())
                        selected_region = st.selectbox(
                            "Select Region",
                            options=regions
                        )
                        
                        region_data = reg_df[reg_df['Region'] == selected_region]
                        
                        fig2 = go.Figure()
                        fig2.add_trace(go.Bar(
                            x=region_data['Scenario'],
                            y=region_data['Prevalence (%)'],
                            marker_color='teal'
                        ))
                        
                        fig2.update_layout(
                            title=f'{selected_region} - HIV Prevalence Comparison',
                            xaxis_title='Scenario',
                            yaxis_title='HIV Prevalence (%)',
                            height=400
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("No regional data available for comparison.")
                else:
                    st.warning("Detailed regional data not available for selected scenarios.")
                    st.info("💡 Run simulations with detailed data collection (e.g., Saint_Seya_Simulation_Detailed)")
        else:
            st.info("Please select at least 2 scenarios to compare.")


def documentation_page():
    """Documentation page."""
    st.markdown('<h2 class="sub-header">Model Documentation</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ## HIVEC-CM: HIV Epidemic Cameroon Model
    
    ### Overview
    HIVEC-CM is an agent-based model (ABM) simulating the HIV epidemic in Cameroon from 1985 to present,
    with projection capabilities to 2100. The model incorporates:
    
    - **Time-varying transmission rates** calibrated to UNAIDS data
    - **Treatment cascade dynamics** (95-95-95 targets)
    - **Policy scenario analysis** (9 different scenarios)
    - **Demographic realism** (age, sex, region, urban/rural)
    
    ### Key Features
    
    #### 1. Time-Varying Transmission
    - **Emergence Phase (1985-1990)**: Low transmission (0.8× multiplier)
    - **Growth Phase (1990-2007)**: Epidemic expansion (6.0× multiplier)  
    - **Decline Phase (2007+)**: ART scale-up (4.0× multiplier)
    
    #### 2. Calibration & Validation
    - ✅ Calibrated against 34 UNAIDS data points (1990-2023)
    - ✅ Mean Absolute Error: 1.73% (target: <2.0%)
    - ✅ All trajectory criteria met
    
    #### 3. Policy Scenarios
    1. **S0**: Baseline (status quo)
    2. **S1a**: Optimistic funding (+20%)
    3. **S1b**: Pessimistic funding (-40%)
    4. **S2a**: Intensified testing
    5. **S2b**: Key populations focus
    6. **S2c**: eTME achievement
    7. **S2d**: Youth & adolescent focus
    8. **S3a**: PSN 2024-2030 aspirational
    9. **S3b**: Geographic prioritization
    
    ### Usage Guide
    
    1. **Configure**: Set parameters in the "Configure & Run" tab
    2. **Select Scenarios**: Choose one or more scenarios to compare
    3. **Run**: Execute the simulation
    4. **Analyze**: View results and download data
    
    ### Technical Details
    
    - **Language**: Python 3.9+
    - **Framework**: Agent-based modeling
    - **Population**: Scalable (1,000 - 1,000,000 agents)
    - **Time step**: 0.1 years (recommended)
    - **Calibration period**: 1985-2023
    - **Projection period**: 2024-2070+
    
    ### References
    - PSN 2024-2030 Strategic Plan (Cameroon MOH)
    - UNAIDS Cameroon Country Data
    - CAMPHIA Survey 2017-2018
    """)


def advanced_settings_page():
    """Advanced settings page."""
    st.markdown('<h2 class="sub-header">Advanced Settings</h2>', unsafe_allow_html=True)
    
    st.warning("⚠️ Advanced settings - modify with caution!")
    
    # System settings
    st.markdown("### System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_cores = st.slider(
            "CPU Cores to Use",
            min_value=1,
            max_value=os.cpu_count(),
            value=max(1, os.cpu_count() - 1),
            help="Number of CPU cores for parallel processing"
        )
        
        memory_limit = st.slider(
            "Memory Limit (GB)",
            min_value=1,
            max_value=64,
            value=8,
            help="Maximum memory allocation"
        )
    
    with col2:
        random_seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=99999,
            value=42,
            help="Set for reproducible results (0 = random)"
        )
        
        debug_mode = st.checkbox(
            "Debug Mode",
            value=False,
            help="Enable verbose logging"
        )
    
    # Model-specific settings
    st.markdown("### Model-Specific Settings")
    
    use_numba = st.checkbox(
        "Use Numba Acceleration",
        value=True,
        help="Enable JIT compilation for faster execution"
    )
    
    mixing_method = st.selectbox(
        "Partner Selection Method",
        options=["binned", "scan"],
        index=0,
        help="Algorithm for partner selection (binned = faster)"
    )
    
    # Clear cache and results
    st.markdown("### Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared!")
    
    with col2:
        if st.button("🧹 Clean Old Results", use_container_width=True):
            st.info("This will remove result directories older than 30 days.")


if __name__ == "__main__":
    main()
