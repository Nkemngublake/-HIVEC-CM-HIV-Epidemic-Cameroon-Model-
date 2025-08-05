"""
Simple analysis utilities for model results
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import logging


def save_analysis_results(analyzer, output_dir):
    """Save analysis results to directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate basic plots
    analyzer.create_simple_dashboard(output_dir)
    
    # Save summary report
    report_path = os.path.join(output_dir, 'analysis_summary.txt')
    with open(report_path, 'w') as f:
        f.write("HIV/AIDS Model Analysis Summary\n")
        f.write("=" * 40 + "\n\n")
        
        indicators = analyzer.calculate_epidemic_indicators()
        for key, value in indicators.items():
            f.write(f"{key}: {value}\n")
    
    logging.info(f"Analysis results saved to {output_dir}")


class ModelAnalyzer:
    """Simple analysis class for model results."""
    
    def __init__(self, results, validation_data=None):
        self.results = results
        self.validation_data = validation_data
    
    def calculate_epidemic_indicators(self):
        """Calculate basic epidemic indicators."""
        # Check for different possible column names
        prevalence_cols = ['HIV_Prevalence', 'hiv_prevalence', 'prevalence']
        prevalence_col = None
        
        for col in prevalence_cols:
            if col in self.results.columns:
                prevalence_col = col
                break
        
        if prevalence_col:
            prevalence = self.results[prevalence_col]
            
            indicators = {
                'peak_prevalence': prevalence.max() * 100,  # Convert to percentage
                'peak_year': 1990 + self.results.loc[prevalence.idxmax(), 'year'] 
                    if 'year' in self.results.columns else
                    1990 + prevalence.idxmax(),
                'final_prevalence': prevalence.iloc[-1] * 100,
                'mean_prevalence': prevalence.mean() * 100
            }
            
            # Check for ART coverage
            art_cols = ['ART_Coverage', 'art_coverage', 'on_art']
            for col in art_cols:
                if col in self.results.columns:
                    if col == 'on_art':
                        # Calculate coverage from counts
                        total_hiv = self.results.get('hiv_infections', 
                                                   self.results.get('HIV_infections', 1))
                        coverage = self.results[col] / total_hiv.replace(0, 1)
                        indicators['final_art_coverage'] = coverage.iloc[-1] * 100
                    else:
                        indicators['final_art_coverage'] = \
                            self.results[col].iloc[-1] * 100
                    break
            
            # Check for infections
            infection_cols = ['Cumulative_Infections', 'hiv_infections', 
                            'new_infections']
            for col in infection_cols:
                if col in self.results.columns:
                    if col == 'new_infections':
                        indicators['total_infections'] = \
                            self.results[col].sum()
                    else:
                        indicators['total_infections'] = \
                            self.results[col].iloc[-1]
                    break
            
            # Check for deaths
            death_cols = ['Deaths', 'deaths_hiv', 'cumulative_deaths']
            for col in death_cols:
                if col in self.results.columns:
                    if col == 'deaths_hiv':
                        indicators['cumulative_deaths'] = \
                            self.results[col].sum()
                    else:
                        indicators['cumulative_deaths'] = \
                            self.results[col].iloc[-1]
                    break
        else:
            indicators = {'error': 'No HIV prevalence data found'}
        
        return indicators
    
    def analyze_transmission_dynamics(self):
        """Analyze transmission dynamics."""
        dynamics = {}
        
        if 'HIV_Prevalence' in self.results.columns:
            prevalence = self.results['HIV_Prevalence']
            
            # Calculate rate of change
            rate_change = np.diff(prevalence)
            dynamics['max_increase_rate'] = rate_change.max()
            dynamics['max_decrease_rate'] = rate_change.min()
            
            # Find turning points
            peaks = []
            for i in range(1, len(rate_change) - 1):
                if rate_change[i-1] > 0 and rate_change[i+1] < 0:
                    peaks.append(i)
            
            dynamics['num_peaks'] = len(peaks)
        
        return dynamics
    
    def analyze_intervention_impact(self):
        """Analyze intervention impact."""
        impact = {}
        
        if 'ART_Coverage' in self.results.columns:
            art_coverage = self.results['ART_Coverage']
            
            # ART scale-up analysis
            art_increase = np.diff(art_coverage)
            impact['art_scale_up_rate'] = art_increase.max()
            
            # Find intervention start (first significant increase)
            intervention_start = None
            for i, increase in enumerate(art_increase):
                if increase > 0.01:  # 1% increase threshold
                    intervention_start = i
                    break
            
            impact['intervention_start_year'] = \
                1990 + intervention_start * 0.1 if intervention_start else None
        
        return impact
    
    def validate_against_real_data(self):
        """Validate model against real data."""
        if self.validation_data is None:
            return None
        
        metrics = {}
        
        try:
            # Match years between simulation and data
            simulated_prev = []
            observed_prev = []
            
            for _, row in self.validation_data.iterrows():
                year = row['Year']
                if year >= 1990 and year <= 2025:
                    time_idx = int((year - 1990) / 0.1)
                    if time_idx < len(self.results):
                        sim_val = self.results.iloc[time_idx]['HIV_Prevalence']
                        obs_val = row['HIV_Prevalence_Rate']
                        
                        simulated_prev.append(sim_val)
                        observed_prev.append(obs_val)
            
            if len(simulated_prev) > 0:
                simulated_prev = np.array(simulated_prev)
                observed_prev = np.array(observed_prev)
                
                # Calculate metrics
                mae = np.mean(np.abs(simulated_prev - observed_prev))
                mse = np.mean((simulated_prev - observed_prev) ** 2)
                
                # R-squared
                ss_tot = np.sum((observed_prev - np.mean(observed_prev)) ** 2)
                ss_res = np.sum((observed_prev - simulated_prev) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                
                # Correlation
                correlation = np.corrcoef(simulated_prev, observed_prev)[0, 1]
                
                metrics = {
                    'mae': mae,
                    'mse': mse,
                    'r_squared': r_squared,
                    'correlation': correlation,
                    'num_points': len(simulated_prev)
                }
            
        except Exception as e:
            logging.warning(f"Validation failed: {e}")
            metrics = {'error': str(e)}
        
        return metrics
    
    def create_simple_dashboard(self, output_dir):
        """Create simple analysis dashboard."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('HIV/AIDS Model Analysis Dashboard', fontsize=16)
        
        # Determine time column
        time_col = 'year' if 'year' in self.results.columns else 'Time'
        if time_col in self.results.columns:
            time_years = self.results[time_col]
        else:
            time_years = 1990 + np.arange(len(self.results))
        
        # Plot 1: HIV Prevalence over time
        prevalence_cols = ['HIV_Prevalence', 'hiv_prevalence', 'prevalence']
        prevalence_col = None
        for col in prevalence_cols:
            if col in self.results.columns:
                prevalence_col = col
                break
        
        if prevalence_col:
            prevalence_data = self.results[prevalence_col] * 100
            axes[0, 0].plot(time_years, prevalence_data)
            axes[0, 0].set_title('HIV Prevalence Over Time')
            axes[0, 0].set_xlabel('Year')
            axes[0, 0].set_ylabel('HIV Prevalence (%)')
            axes[0, 0].grid(True, alpha=0.3)
            
            # Add validation data if available
            if self.validation_data is not None:
                axes[0, 0].scatter(
                    self.validation_data['Year'],
                    self.validation_data['HIV_Prevalence_Rate'],
                    color='red', alpha=0.7, label='Observed data'
                )
                axes[0, 0].legend()
        
        # Plot 2: Population dynamics
        pop_cols = ['total_population', 'Total_Population', 'population']
        pop_col = None
        for col in pop_cols:
            if col in self.results.columns:
                pop_col = col
                break
        
        if pop_col:
            axes[0, 1].plot(time_years, self.results[pop_col])
            axes[0, 1].set_title('Population Over Time')
            axes[0, 1].set_xlabel('Year')
            axes[0, 1].set_ylabel('Population')
            axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: HIV infections
        infection_cols = ['hiv_infections', 'HIV_infections', 'infections']
        infection_col = None
        for col in infection_cols:
            if col in self.results.columns:
                infection_col = col
                break
        
        if infection_col:
            axes[1, 0].plot(time_years, self.results[infection_col])
            axes[1, 0].set_title('HIV Infections Over Time')
            axes[1, 0].set_xlabel('Year')
            axes[1, 0].set_ylabel('HIV Infections')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: New infections
        new_infection_cols = ['new_infections', 'New_Infections']
        new_infection_col = None
        for col in new_infection_cols:
            if col in self.results.columns:
                new_infection_col = col
                break
        
        if new_infection_col:
            axes[1, 1].plot(time_years, self.results[new_infection_col])
            axes[1, 1].set_title('New HIV Infections Over Time')
            axes[1, 1].set_xlabel('Year')
            axes[1, 1].set_ylabel('New Infections')
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save dashboard
        dashboard_path = os.path.join(output_dir, 'analysis_dashboard.png')
        plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logging.info(f"Dashboard saved to {dashboard_path}")
