"""
Advanced Analysis and Visualization Module
=========================================

Comprehensive analysis tools for HIV/AIDS epidemic model results
including statistical analysis, visualization, and validation.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Set matplotlib style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class ModelAnalyzer:
    """
    Comprehensive analysis tool for HIV epidemic model results.
    """
    
    def __init__(self, results: pd.DataFrame, real_data: Optional[pd.DataFrame] = None):
        """
        Initialize analyzer with model results and optional real data.
        
        Args:
            results: Model simulation results
            real_data: Real epidemiological data for comparison
        """
        self.results = results
        self.real_data = real_data
        self.analysis_results = {}
        
    def calculate_epidemic_indicators(self) -> Dict:
        """Calculate key epidemiological indicators."""
        indicators = {}
        
        # Peak epidemic characteristics
        peak_prevalence = self.results['hiv_prevalence'].max()
        peak_year_idx = self.results['hiv_prevalence'].idxmax()
        peak_year = self.results.iloc[peak_year_idx]['year']
        
        # Epidemic trajectory
        final_prevalence = self.results['hiv_prevalence'].iloc[-1]
        prevalence_decline = peak_prevalence - final_prevalence
        
        # Incidence dynamics
        max_incidence_rate = (self.results['new_infections'] / 
                             self.results['total_population'] * 1000).max()
        
        # Treatment coverage
        final_art_coverage = self.results['art_coverage'].iloc[-1]
        art_scale_up_rate = self._calculate_art_scale_up_rate()
        
        # Population impact
        total_infections = self.results['hiv_infections'].iloc[-1]
        cumulative_deaths = self._estimate_cumulative_deaths()
        
        indicators = {
            'peak_prevalence': peak_prevalence,
            'peak_year': peak_year,
            'final_prevalence': final_prevalence,
            'prevalence_decline': prevalence_decline,
            'max_incidence_rate': max_incidence_rate,
            'final_art_coverage': final_art_coverage,
            'art_scale_up_rate': art_scale_up_rate,
            'total_infections': total_infections,
            'cumulative_deaths': cumulative_deaths
        }
        
        self.analysis_results['epidemic_indicators'] = indicators
        return indicators
    
    def _calculate_art_scale_up_rate(self) -> float:
        """Calculate ART scale-up rate per year."""
        art_data = self.results[self.results['year'] >= 2005].copy()
        if len(art_data) < 2:
            return 0.0
        
        # Linear regression of ART coverage over time
        years = art_data['year'] - 2005
        coverage = art_data['art_coverage']
        
        if len(years) > 1 and coverage.std() > 0:
            slope = np.polyfit(years, coverage, 1)[0]
            return max(0, slope)
        return 0.0
    
    def _estimate_cumulative_deaths(self) -> int:
        """Estimate cumulative HIV-related deaths."""
        # Simple estimation based on mortality rates
        total_deaths = sum(self.results['deaths_hiv'])
        return int(total_deaths)
    
    def analyze_transmission_dynamics(self) -> Dict:
        """Analyze HIV transmission dynamics over time."""
        # Calculate effective reproduction number (simplified)
        reproduction_numbers = []
        
        for i in range(1, len(self.results)):
            new_infections = self.results.iloc[i]['new_infections']
            prev_infections = self.results.iloc[i-1]['hiv_infections']
            
            if prev_infections > 0:
                # Simplified R calculation
                r_eff = new_infections / (prev_infections * 0.1)  # Approximate infectious period
                reproduction_numbers.append(min(r_eff, 5.0))  # Cap at 5
            else:
                reproduction_numbers.append(0.0)
        
        # Transmission intensity over time
        incidence_rate = (self.results['new_infections'] / 
                         self.results['total_population'] * 1000)
        
        # Force of infection
        force_of_infection = (self.results['new_infections'] / 
                             self.results['susceptible'])
        force_of_infection = force_of_infection.fillna(0)
        
        dynamics = {
            'reproduction_numbers': reproduction_numbers,
            'incidence_rate': incidence_rate.tolist(),
            'force_of_infection': force_of_infection.tolist(),
            'peak_transmission_year': self.results.iloc[incidence_rate.idxmax()]['year']
        }
        
        self.analysis_results['transmission_dynamics'] = dynamics
        return dynamics
    
    def analyze_intervention_impact(self) -> Dict:
        """Analyze impact of interventions (testing and treatment)."""
        # Pre/post ART comparison
        pre_art = self.results[self.results['year'] < 2005]
        post_art = self.results[self.results['year'] >= 2005]
        
        if len(pre_art) > 0 and len(post_art) > 0:
            pre_art_trend = np.polyfit(pre_art['year'] - pre_art['year'].min(), 
                                      pre_art['hiv_prevalence'], 1)[0]
            post_art_trend = np.polyfit(post_art['year'] - post_art['year'].min(), 
                                       post_art['hiv_prevalence'], 1)[0]
        else:
            pre_art_trend = post_art_trend = 0.0
        
        # Treatment cascade analysis
        if len(post_art) > 0:
            final_cascade = {
                'infected': post_art['hiv_infections'].iloc[-1],
                'tested': post_art['tested'].iloc[-1],
                'diagnosed': post_art['diagnosed'].iloc[-1],
                'on_treatment': post_art['on_art'].iloc[-1]
            }
            
            cascade_proportions = {
                'testing_rate': final_cascade['tested'] / final_cascade['infected'] if final_cascade['infected'] > 0 else 0,
                'diagnosis_rate': final_cascade['diagnosed'] / final_cascade['infected'] if final_cascade['infected'] > 0 else 0,
                'treatment_rate': final_cascade['on_treatment'] / final_cascade['infected'] if final_cascade['infected'] > 0 else 0
            }
        else:
            cascade_proportions = {'testing_rate': 0, 'diagnosis_rate': 0, 'treatment_rate': 0}
        
        # Estimate infections averted by ART
        if len(post_art) > 5:
            # Compare actual trend with extrapolated pre-ART trend
            years_since_art = post_art['year'] - 2005
            expected_without_art = (pre_art['hiv_prevalence'].iloc[-1] + 
                                   pre_art_trend * years_since_art)
            actual_prevalence = post_art['hiv_prevalence']
            
            # Estimate cumulative difference
            prevalence_difference = expected_without_art - actual_prevalence
            prevalence_difference = prevalence_difference.clip(lower=0)
            
            avg_population = post_art['total_population'].mean()
            infections_averted = (prevalence_difference / 100 * avg_population).sum()
        else:
            infections_averted = 0
        
        intervention_impact = {
            'pre_art_trend': pre_art_trend,
            'post_art_trend': post_art_trend,
            'trend_change': post_art_trend - pre_art_trend,
            'cascade_proportions': cascade_proportions,
            'estimated_infections_averted': int(infections_averted)
        }
        
        self.analysis_results['intervention_impact'] = intervention_impact
        return intervention_impact
    
    def validate_against_real_data(self) -> Optional[Dict]:
        """Validate model results against real data."""
        if self.real_data is None:
            return None
        
        # Find overlapping years
        common_years = set(self.results['year']) & set(self.real_data['Year'])

        # Determine real prevalence column (assumed in percent)
        real_prev_col = None
        for col in ['HIV Prevalence', 'HIV_Prevalence_Rate']:
            if col in self.real_data.columns:
                real_prev_col = col
                break
        if real_prev_col is None:
            return None

        validation_data = []
        for year in sorted(common_years):
            real_prev = self.real_data[self.real_data['Year'] == year][real_prev_col].iloc[0]
            model_prev_prop = self.results[self.results['year'] == year]['hiv_prevalence'].iloc[0]
            model_prev = model_prev_prop * 100.0  # convert to percent for comparison

            if not pd.isna(real_prev):
                validation_data.append({
                    'year': year,
                    'real_prevalence': real_prev,
                    'model_prevalence': model_prev,
                    'absolute_error': abs(real_prev - model_prev),
                    'relative_error': abs(real_prev - model_prev) / real_prev * 100 if real_prev > 0 else 0
                })
        
        if not validation_data:
            return None
        
        val_df = pd.DataFrame(validation_data)
        
        # Calculate summary metrics
        validation_metrics = {
            'mae': val_df['absolute_error'].mean(),
            'rmse': np.sqrt(val_df['absolute_error'].pow(2).mean()),
            'mape': val_df['relative_error'].mean(),
            'max_error': val_df['absolute_error'].max(),
            'r_squared': self._calculate_r_squared(val_df['real_prevalence'], val_df['model_prevalence']),
            'correlation': val_df[['real_prevalence', 'model_prevalence']].corr().iloc[0, 1],
            'n_points': len(validation_data)
        }
        
        self.analysis_results['validation'] = {
            'metrics': validation_metrics,
            'data': validation_data
        }
        
        return validation_metrics
    
    def _calculate_r_squared(self, actual: pd.Series, predicted: pd.Series) -> float:
        """Calculate R-squared coefficient."""
        ss_res = ((actual - predicted) ** 2).sum()
        ss_tot = ((actual - actual.mean()) ** 2).sum()
        
        if ss_tot == 0:
            return 0.0
        
        return 1 - (ss_res / ss_tot)
    
    def create_comprehensive_dashboard(self, save_path: Optional[str] = None) -> plt.Figure:
        """Create comprehensive analysis dashboard."""
        fig = plt.figure(figsize=(20, 24))
        
        # Define grid layout
        gs = fig.add_gridspec(6, 3, hspace=0.3, wspace=0.3)
        
        # 1. HIV Prevalence Over Time
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_prevalence_trends(ax1)
        
        # 2. Population Dynamics
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_population_dynamics(ax2)
        
        # 3. Disease Stage Distribution
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_disease_stages(ax3)
        
        # 4. Treatment Cascade
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_treatment_cascade(ax4)
        
        # 5. Incidence Rate
        ax5 = fig.add_subplot(gs[1, 2])
        self._plot_incidence_rate(ax5)
        
        # 6. Validation (if real data available)
        ax6 = fig.add_subplot(gs[2, 0])
        self._plot_validation(ax6)
        
        # 7. Epidemic Curve Phases
        ax7 = fig.add_subplot(gs[2, 1])
        self._plot_epidemic_phases(ax7)
        
        # 8. Age Structure Impact (simplified)
        ax8 = fig.add_subplot(gs[2, 2])
        self._plot_demographic_impact(ax8)
        
        # 9. Transmission Dynamics
        ax9 = fig.add_subplot(gs[3, :])
        self._plot_transmission_dynamics(ax9)
        
        # 10. Intervention Timeline
        ax10 = fig.add_subplot(gs[4, :])
        self._plot_intervention_timeline(ax10)
        
        # 11. Summary Statistics
        ax11 = fig.add_subplot(gs[5, :])
        self._plot_summary_statistics(ax11)
        
        plt.suptitle('HIV/AIDS Epidemic Model: Comprehensive Analysis Dashboard', 
                     fontsize=20, fontweight='bold', y=0.98)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Dashboard saved to {save_path}")
        
        return fig
    
    def _plot_prevalence_trends(self, ax):
        """Plot HIV prevalence trends with real data comparison."""
        # Model prevalence stored as proportion; plot in %
        ax.plot(
            self.results['year'],
            self.results['hiv_prevalence'] * 100.0,
            'b-',
            linewidth=3,
            label='Model',
            alpha=0.8,
        )

        if self.real_data is not None:
            # Support multiple column names for real prevalence
            real_prev_col = None
            for col in ['HIV Prevalence', 'HIV_Prevalence_Rate']:
                if col in self.real_data.columns:
                    real_prev_col = col
                    break
            if real_prev_col is not None:
                mask = self.real_data[real_prev_col].notna()
                ax.plot(
                    self.real_data[mask]['Year'],
                    self.real_data[mask][real_prev_col],
                    'ro-',
                    linewidth=2,
                    markersize=6,
                    label='Real Data',
                    alpha=0.7,
                )
        
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('HIV Prevalence (%)', fontsize=12)
        ax.set_title('HIV Prevalence Trends', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Add annotations for key events
        ax.axvline(x=2005, color='red', linestyle='--', alpha=0.5, label='ART Introduction')
        ax.text(2005.5, ax.get_ylim()[1]*0.9, 'ART\nIntroduced', fontsize=10, alpha=0.7)
    
    def _plot_population_dynamics(self, ax):
        """Plot population dynamics."""
        years = self.results['year']
        
        ax.fill_between(years, 0, self.results['susceptible'], 
                       alpha=0.7, label='Susceptible', color='green')
        ax.fill_between(years, self.results['susceptible'], 
                       self.results['susceptible'] + self.results['hiv_infections'],
                       alpha=0.7, label='HIV+', color='red')
        
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Population', fontsize=12)
        ax.set_title('Population Dynamics', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
    
    def _plot_disease_stages(self, ax):
        """Plot disease stage distribution over time."""
        years = self.results['year']
        
        ax.plot(years, self.results['acute'], 'orange', linewidth=2, label='Acute')
        ax.plot(years, self.results['chronic'], 'blue', linewidth=2, label='Chronic')
        ax.plot(years, self.results['aids'], 'red', linewidth=2, label='AIDS')
        
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Number of Cases', fontsize=12)
        ax.set_title('HIV Disease Stages', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
    
    def _plot_treatment_cascade(self, ax):
        """Plot treatment cascade evolution."""
        final_year_data = self.results.iloc[-1]
        
        cascade_values = [
            final_year_data['hiv_infections'],
            final_year_data['tested'],
            final_year_data['diagnosed'],
            final_year_data['on_art']
        ]
        
        cascade_labels = ['HIV+', 'Tested', 'Diagnosed', 'On ART']
        colors = ['red', 'orange', 'yellow', 'green']
        
        bars = ax.bar(cascade_labels, cascade_values, color=colors, alpha=0.7)
        
        # Add percentage labels
        for i, (bar, value) in enumerate(zip(bars, cascade_values)):
            if i > 0 and cascade_values[0] > 0:
                percentage = value / cascade_values[0] * 100
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                       f'{percentage:.1f}%', ha='center', fontsize=10)
        
        ax.set_ylabel('Number of People', fontsize=12)
        ax.set_title('Treatment Cascade (Final Year)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_incidence_rate(self, ax):
        """Plot HIV incidence rate over time."""
        incidence_rate = (self.results['new_infections'] / 
                         self.results['total_population'] * 1000)
        
        ax.plot(self.results['year'], incidence_rate, 'purple', linewidth=2)
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Incidence Rate (per 1000)', fontsize=12)
        ax.set_title('HIV Incidence Rate', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    def _plot_validation(self, ax):
        """Plot model validation against real data."""
        if 'validation' in self.analysis_results:
            val_data = self.analysis_results['validation']['data']
            val_df = pd.DataFrame(val_data)
            
            ax.plot(val_df['year'], val_df['absolute_error'], 'ro-', linewidth=2)
            ax.set_xlabel('Year', fontsize=12)
            ax.set_ylabel('Absolute Error (%)', fontsize=12)
            ax.set_title('Model Validation Error', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add mean error line
            mean_error = val_df['absolute_error'].mean()
            ax.axhline(y=mean_error, color='red', linestyle='--', 
                      label=f'Mean Error: {mean_error:.2f}%')
            ax.legend(fontsize=10)
        else:
            ax.text(0.5, 0.5, 'No validation\ndata available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Model Validation', fontsize=14, fontweight='bold')
    
    def _plot_epidemic_phases(self, ax):
        """Plot epidemic phases (growth, peak, decline)."""
        # Convert prevalence to percent for visualization
        prevalence = self.results['hiv_prevalence'] * 100.0
        years = self.results['year']
        
        # Find peak
        peak_idx = prevalence.idxmax()
        peak_year = years.iloc[peak_idx]
        
        # Growth phase
        growth_phase = years <= peak_year
        ax.fill_between(years[growth_phase], 0, prevalence[growth_phase], 
                       alpha=0.3, color='red', label='Growth Phase')
        
        # Decline phase
        decline_phase = years > peak_year
        if decline_phase.any():
            ax.fill_between(years[decline_phase], 0, prevalence[decline_phase], 
                           alpha=0.3, color='blue', label='Decline Phase')
        
        ax.plot(years, prevalence, 'black', linewidth=2)
        ax.axvline(x=peak_year, color='red', linestyle='--', alpha=0.7)
        
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('HIV Prevalence (%)', fontsize=12)
        ax.set_title('Epidemic Phases', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
    
    def _plot_demographic_impact(self, ax):
        """Plot simplified demographic impact."""
        # Show proportion of population affected
        total_pop = self.results['total_population']
        hiv_pop = self.results['hiv_infections']
        
        proportion_affected = hiv_pop / total_pop * 100
        
        ax.fill_between(self.results['year'], 0, proportion_affected, 
                       alpha=0.6, color='red')
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Population Affected (%)', fontsize=12)
        ax.set_title('Demographic Impact', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    def _plot_transmission_dynamics(self, ax):
        """Plot transmission dynamics analysis."""
        if 'transmission_dynamics' in self.analysis_results:
            dynamics = self.analysis_results['transmission_dynamics']
            
            # Primary axis: incidence rate
            ax.plot(self.results['year'], dynamics['incidence_rate'], 
                   'red', linewidth=2, label='Incidence Rate')
            ax.set_ylabel('Incidence Rate (per 1000)', color='red', fontsize=12)
            ax.tick_params(axis='y', labelcolor='red')
            
            # Secondary axis: force of infection
            ax2 = ax.twinx()
            ax2.plot(self.results['year'], dynamics['force_of_infection'], 
                    'blue', linewidth=2, label='Force of Infection')
            ax2.set_ylabel('Force of Infection', color='blue', fontsize=12)
            ax2.tick_params(axis='y', labelcolor='blue')
            
            ax.set_xlabel('Year', fontsize=12)
            ax.set_title('Transmission Dynamics', fontsize=16, fontweight='bold')
            ax.grid(True, alpha=0.3)
    
    def _plot_intervention_timeline(self, ax):
        """Plot intervention impact timeline."""
        years = self.results['year']
        
        # Show multiple indicators
        # Prevalence as percent for display
        ax.plot(years, self.results['hiv_prevalence'] * 100.0, 'red', linewidth=3, 
               label='HIV Prevalence (%)')
        
        # Normalize ART coverage to same scale
        # Convert coverage to percent then scale for visibility
        art_coverage_norm = (self.results['art_coverage'] * 100.0) / 10
        ax.plot(years, art_coverage_norm, 'green', linewidth=2, 
               label='ART Coverage (%, ÷10)')
        
        # Show intervention milestones
        ax.axvline(x=2005, color='blue', linestyle='--', alpha=0.7, 
                  label='ART Introduction')
        ax.axvline(x=2010, color='orange', linestyle='--', alpha=0.7, 
                  label='Treatment Scale-up')
        
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Prevalence (%) / Coverage (÷10)', fontsize=12)
        ax.set_title('Intervention Impact Timeline', fontsize=16, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
    
    def _plot_summary_statistics(self, ax):
        """Plot summary statistics table."""
        ax.axis('off')
        
        # Calculate key statistics
        if 'epidemic_indicators' in self.analysis_results:
            indicators = self.analysis_results['epidemic_indicators']
            
            stats_text = f"""
KEY EPIDEMIC INDICATORS:
• Peak Prevalence: {indicators['peak_prevalence'] * 100:.1f}% (Year: {indicators['peak_year']:.0f})
• Final Prevalence: {indicators['final_prevalence'] * 100:.1f}%
• Prevalence Decline: {indicators['prevalence_decline'] * 100:.1f} percentage points
• Final ART Coverage: {indicators['final_art_coverage'] * 100:.1f}%
• Total HIV Infections: {indicators['total_infections']:,}
• Estimated Deaths: {indicators['cumulative_deaths']:,}

TRANSMISSION DYNAMICS:
• Peak Incidence Rate: {indicators['max_incidence_rate']:.2f} per 1000
• ART Scale-up Rate: {indicators['art_scale_up_rate'] * 100:.1f}% per year
"""
            
            if 'validation' in self.analysis_results:
                val_metrics = self.analysis_results['validation']['metrics']
                stats_text += f"""
MODEL VALIDATION:
• Mean Absolute Error: {val_metrics['mae']:.2f} percentage points
• Root Mean Squared Error: {val_metrics['rmse']:.2f}
• Correlation with Real Data: {val_metrics['correlation']:.3f}
• R-squared: {val_metrics['r_squared']:.3f}
"""
            
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                   fontsize=11, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive text report."""
        report_lines = []
        report_lines.append("HIV/AIDS EPIDEMIC MODEL - COMPREHENSIVE ANALYSIS REPORT")
        report_lines.append("=" * 70)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Run all analyses
        epidemic_indicators = self.calculate_epidemic_indicators()
        transmission_dynamics = self.analyze_transmission_dynamics()
        intervention_impact = self.analyze_intervention_impact()
        validation_metrics = self.validate_against_real_data()
        
        # Epidemic Overview
        report_lines.append("EPIDEMIC OVERVIEW:")
        report_lines.append("-" * 20)
        report_lines.append(f"Simulation Period: {self.results['year'].min():.0f} - {self.results['year'].max():.0f}")
        report_lines.append(f"Initial Population: {self.results['total_population'].iloc[0]:,}")
        report_lines.append(f"Final Population: {self.results['total_population'].iloc[-1]:,}")
        report_lines.append("")
        
        # Epidemic Characteristics
        report_lines.append("EPIDEMIC CHARACTERISTICS:")
        report_lines.append("-" * 25)
        report_lines.append(f"Peak HIV Prevalence: {epidemic_indicators['peak_prevalence']:.2f}% (Year: {epidemic_indicators['peak_year']:.0f})")
        report_lines.append(f"Final HIV Prevalence: {epidemic_indicators['final_prevalence']:.2f}%")
        report_lines.append(f"Prevalence Decline: {epidemic_indicators['prevalence_decline']:.2f} percentage points")
        report_lines.append(f"Maximum Incidence Rate: {epidemic_indicators['max_incidence_rate']:.2f} per 1,000 population")
        report_lines.append(f"Total HIV Infections (final): {epidemic_indicators['total_infections']:,}")
        report_lines.append(f"Estimated HIV Deaths: {epidemic_indicators['cumulative_deaths']:,}")
        report_lines.append("")
        
        # Treatment and Care
        report_lines.append("TREATMENT AND CARE:")
        report_lines.append("-" * 20)
        report_lines.append(
            f"Final ART Coverage: {epidemic_indicators['final_art_coverage'] * 100:.1f}%"
        )
        report_lines.append(
            f"ART Scale-up Rate: {epidemic_indicators['art_scale_up_rate'] * 100:.1f}% per year"
        )
        
        cascade = intervention_impact['cascade_proportions']
        report_lines.append(f"Testing Rate: {cascade['testing_rate']*100:.1f}%")
        report_lines.append(f"Diagnosis Rate: {cascade['diagnosis_rate']*100:.1f}%")
        report_lines.append(f"Treatment Rate: {cascade['treatment_rate']*100:.1f}%")
        report_lines.append("")
        
        # Intervention Impact
        report_lines.append("INTERVENTION IMPACT:")
        report_lines.append("-" * 20)
        report_lines.append(f"Pre-ART Trend: {intervention_impact['pre_art_trend']:.3f}% per year")
        report_lines.append(f"Post-ART Trend: {intervention_impact['post_art_trend']:.3f}% per year")
        report_lines.append(f"Trend Change: {intervention_impact['trend_change']:.3f}% per year")
        report_lines.append(f"Estimated Infections Averted: {intervention_impact['estimated_infections_averted']:,}")
        report_lines.append("")
        
        # Model Validation
        if validation_metrics:
            report_lines.append("MODEL VALIDATION:")
            report_lines.append("-" * 17)
            report_lines.append(f"Mean Absolute Error: {validation_metrics['mae']:.2f} percentage points")
            report_lines.append(f"Root Mean Squared Error: {validation_metrics['rmse']:.2f}")
            report_lines.append(f"Mean Absolute Percentage Error: {validation_metrics['mape']:.1f}%")
            report_lines.append(f"R-squared: {validation_metrics['r_squared']:.3f}")
            report_lines.append(f"Correlation: {validation_metrics['correlation']:.3f}")
            report_lines.append(f"Validation Points: {validation_metrics['n_points']}")
        else:
            report_lines.append("MODEL VALIDATION: No real data available for comparison")
        
        report_lines.append("")
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)


def save_analysis_results(analyzer: ModelAnalyzer, output_dir: str):
    """Save all analysis results to files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate comprehensive dashboard
    fig = analyzer.create_comprehensive_dashboard()
    dashboard_path = os.path.join(output_dir, 'comprehensive_analysis_dashboard.png')
    fig.savefig(dashboard_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Generate and save report
    report = analyzer.generate_comprehensive_report()
    report_path = os.path.join(output_dir, 'comprehensive_analysis_report.txt')
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Save analysis results as JSON
    import json
    results_path = os.path.join(output_dir, 'analysis_results.json')
    
    # Convert numpy types to native Python types for JSON serialization
    serializable_results = {}
    for key, value in analyzer.analysis_results.items():
        if isinstance(value, dict):
            serializable_results[key] = {k: float(v) if isinstance(v, np.number) else v 
                                       for k, v in value.items() if not isinstance(v, (list, np.ndarray))}
    
    with open(results_path, 'w') as f:
        json.dump(serializable_results, f, indent=2, default=str)
    
    logger.info(f"Analysis results saved to {output_dir}")


def main():
    """Main analysis execution."""
    # Load model results
    try:
        results = pd.read_csv('results/enhanced_hiv_model_results.csv')
        logger.info("Loaded enhanced model results")
    except FileNotFoundError:
        try:
            results = pd.read_csv('model_outputs/hiv_model_results.csv')
            logger.info("Loaded basic model results")
        except FileNotFoundError:
            logger.error("No model results found")
            return
    
    # Load real data if available
    try:
        real_data = pd.read_csv('data/processed/integrated_hiv_cameroon_data.csv')
        logger.info("Loaded real data for validation")
    except FileNotFoundError:
        real_data = None
        logger.warning("No real data available for validation")
    
    # Initialize analyzer
    analyzer = ModelAnalyzer(results, real_data)
    
    # Run comprehensive analysis
    logger.info("Running comprehensive analysis...")
    save_analysis_results(analyzer, 'results/analysis')
    
    print("\nComprehensive Analysis Completed!")
    print("Check 'results/analysis/' directory for outputs:")
    print("- comprehensive_analysis_dashboard.png")
    print("- comprehensive_analysis_report.txt")
    print("- analysis_results.json")


if __name__ == "__main__":
    main()
