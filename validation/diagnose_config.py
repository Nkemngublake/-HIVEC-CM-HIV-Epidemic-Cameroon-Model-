#!/usr/bin/env python3
"""
Model Configuration Diagnostic Tool
====================================
Analyzes model configuration and identifies scale issues for validation.

This tool examines:
1. Population size (agents vs. real population)
2. Unit conversions needed for validation
3. Scaling factors for outputs
4. Parameter values affecting calibration

Usage:
    python diagnose_config.py
    python diagnose_config.py --show-conversions
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse


class ModelDiagnostic:
    """Diagnostic tool for model configuration."""
    
    def __init__(self, config_path='../config/parameters.json', 
                 results_path='../results/montecarlo_scenarios/S0_baseline/20251012_003019'):
        self.config_path = Path(config_path)
        self.results_path = Path(results_path)
        
        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        # Load run configuration
        run_config_path = self.results_path / 'run_config.json'
        if run_config_path.exists():
            with open(run_config_path, 'r') as f:
                self.run_config = json.load(f)
        else:
            self.run_config = None
        
        # Real Cameroon data (1990 baseline)
        self.real_cameroon = {
            'population_1990': 11900000,  # 11.9 million
            'population_2023': 28300000,  # 28.3 million
            'hiv_prevalence_1990': 0.005,  # 0.5%
            'hiv_prevalence_2023': 0.034,  # 3.4%
        }
    
    def check_population_size(self):
        """Check population size configuration."""
        print("\n" + "="*60)
        print("POPULATION SIZE ANALYSIS")
        print("="*60)
        
        model_pop = self.config['parameters']['population']['initial_population']
        run_pop = self.run_config.get('population_size', 'N/A') if self.run_config else 'N/A'
        real_pop = self.real_cameroon['population_1990']
        
        print(f"\n📊 Population Configuration:")
        print(f"   Config File:      {model_pop:,} agents")
        print(f"   Actual Run:       {run_pop:,} agents" if run_pop != 'N/A' else f"   Actual Run:       {run_pop}")
        print(f"   Real Cameroon:    {real_pop:,} people (1990)")
        
        if run_pop != 'N/A':
            scale_factor = real_pop / run_pop
            print(f"\n⚠️  SCALE MISMATCH:")
            print(f"   Model is {scale_factor:,.1f}× smaller than reality")
            print(f"   1 model agent represents ~{scale_factor:,.0f} real people")
        
        return run_pop if run_pop != 'N/A' else model_pop
    
    def check_output_units(self):
        """Check units in model outputs."""
        print("\n" + "="*60)
        print("OUTPUT UNITS ANALYSIS")
        print("="*60)
        
        summary_path = self.results_path / 'summary_statistics.csv'
        if not summary_path.exists():
            print("   ⚠️  No summary statistics found")
            return
        
        df = pd.read_csv(summary_path)
        
        # Check sample values
        sample_year = 2000
        sample_data = df[df['year'] == sample_year].iloc[0] if sample_year in df['year'].values else df.iloc[10]
        
        print(f"\n📈 Sample Output Values (Year {int(sample_data['year'])}):")
        print(f"   HIV Prevalence:        {sample_data['hiv_prevalence_mean']:.6f}")
        print(f"   Population:            {sample_data['total_population_mean']:.1f}")
        print(f"   New Infections:        {sample_data['new_infections_mean']:.1f}")
        print(f"   HIV Deaths:            {sample_data['deaths_hiv_mean']:.1f}")
        
        print(f"\n💡 Unit Interpretation:")
        print(f"   Prevalence:    Stored as proportion (0-1), should be % (0-100) for UNAIDS")
        print(f"   Population:    Agent count, should be thousands for UN/UNAIDS")
        print(f"   Infections:    Raw count, should be thousands for UNAIDS")
        print(f"   Deaths:        Raw count, should be thousands for UNAIDS")
        
        return df
    
    def calculate_scaling_factors(self, model_pop):
        """Calculate required scaling factors."""
        print("\n" + "="*60)
        print("SCALING FACTORS FOR VALIDATION")
        print("="*60)
        
        real_pop = self.real_cameroon['population_1990']
        population_scale = real_pop / model_pop
        
        print(f"\n🔧 Required Conversions:")
        print(f"   1. Prevalence:    model_value × 100          → percentage")
        print(f"   2. Population:    model_value × {population_scale/1000:.1f} / 1000  → thousands")
        print(f"   3. Infections:    model_value × {population_scale:.1f} / 1000 → thousands")
        print(f"   4. Deaths:        model_value × {population_scale:.1f} / 1000 → thousands")
        print(f"   5. PLHIV:         prevalence × population    → thousands")
        
        return {
            'population_scale': population_scale,
            'to_thousands': population_scale / 1000,
            'to_percentage': 100
        }
    
    def check_transmission_parameters(self):
        """Check key transmission parameters."""
        print("\n" + "="*60)
        print("TRANSMISSION PARAMETERS")
        print("="*60)
        
        hiv_params = self.config['parameters']['hiv_transmission']
        
        print(f"\n🦠 HIV Transmission Configuration:")
        print(f"   Base transmission probability:")
        print(f"      Acute:    {hiv_params['transmission_probability']['acute']:.4f}")
        print(f"      Chronic:  {hiv_params['transmission_probability']['chronic']:.4f}")
        print(f"      AIDS:     {hiv_params['transmission_probability']['aids']:.4f}")
        print(f"      On ART:   {hiv_params['transmission_probability']['on_art']:.4f}")
        
        print(f"\n   Contact rates (per year):")
        contact_params = hiv_params.get('contact_patterns', {})
        if contact_params:
            for key, value in contact_params.items():
                print(f"      {key}: {value}")
        else:
            print(f"      Not specified in config (using model defaults)")
        
        print(f"\n   Initial seeding:")
        print(f"      Initial HIV+ fraction: Not specified in config")
        print(f"      Model will need calibration to match 1990 prevalence")
    
    def recommend_fixes(self, scaling_factors):
        """Provide specific recommendations."""
        print("\n" + "="*60)
        print("RECOMMENDED FIXES")
        print("="*60)
        
        print(f"\n🎯 Priority 1: Add Scaling to Validation Script")
        print(f"   File: validation/quick_validate.py")
        print(f"   Add to load_model_results():")
        print(f"   ```python")
        print(f"   # Apply scaling factors")
        print(f"   df['hiv_prevalence_pct'] = df['hiv_prevalence_mean'] * 100")
        print(f"   df['population_thousands'] = df['total_population_mean'] * {scaling_factors['to_thousands']:.2f}")
        print(f"   df['infections_thousands'] = df['new_infections_mean'] * {scaling_factors['to_thousands']:.2f}")
        print(f"   df['deaths_thousands'] = df['deaths_hiv_mean'] * {scaling_factors['to_thousands']:.2f}")
        print(f"   df['plhiv_thousands'] = df['plhiv'] * {scaling_factors['to_thousands']:.2f}")
        print(f"   ```")
        
        print(f"\n🎯 Priority 2: Run with Full-Scale Population")
        print(f"   Option A: Increase population to ~1 million agents")
        print(f"             (computationally expensive)")
        print(f"   ")
        print(f"   Option B: Keep 10k agents but interpret as scaled")
        print(f"             Each agent represents ~1,190 people")
        print(f"             Apply scaling in post-processing (RECOMMENDED)")
        
        print(f"\n🎯 Priority 3: Calibrate Transmission Parameters")
        print(f"   Target: Match UNAIDS 1990 prevalence (0.5%)")
        print(f"   Adjust:")
        print(f"      - Initial seeding (number of HIV+ agents in 1985-1990)")
        print(f"      - Base transmission probability")
        print(f"      - Contact rates by risk group")
        print(f"   Tool: Use automated calibration script (see calibrate_model.py)")
        
        print(f"\n🎯 Priority 4: Update Validation Targets")
        print(f"   Current: UNAIDS data in absolute thousands")
        print(f"   Options:")
        print(f"      A) Scale targets down to model scale")
        print(f"      B) Scale model outputs up to real scale (RECOMMENDED)")
    
    def generate_summary_report(self, model_pop, scaling_factors):
        """Generate summary report."""
        print("\n" + "="*60)
        print("DIAGNOSTIC SUMMARY")
        print("="*60)
        
        issues = []
        
        # Check 1: Population scale
        if model_pop < 100000:
            issues.append({
                'severity': 'HIGH',
                'issue': 'Small population size',
                'impact': 'Model outputs need ~1200× scaling for validation',
                'solution': 'Apply post-processing scaling or increase population'
            })
        
        # Check 2: Units
        issues.append({
            'severity': 'HIGH',
            'issue': 'Unit mismatch',
            'impact': 'Prevalence in proportions, not percentages',
            'solution': 'Multiply prevalence by 100 in validation'
        })
        
        # Check 3: Calibration
        issues.append({
            'severity': 'HIGH',
            'issue': 'Model not calibrated to UNAIDS data',
            'impact': 'Large discrepancies in prevalence trajectory',
            'solution': 'Run automated calibration (calibrate_model.py)'
        })
        
        print(f"\n🔍 Issues Identified: {len(issues)}")
        for i, issue in enumerate(issues, 1):
            print(f"\n   Issue {i} [{issue['severity']}]: {issue['issue']}")
            print(f"   Impact:   {issue['impact']}")
            print(f"   Solution: {issue['solution']}")
        
        # Save to file
        report_path = Path('validation_outputs/diagnostic_report.json')
        report_path.parent.mkdir(exist_ok=True)
        
        report = {
            'model_configuration': {
                'population_size': int(model_pop),
                'real_population_1990': self.real_cameroon['population_1990'],
                'scale_factor': scaling_factors['population_scale']
            },
            'scaling_factors': scaling_factors,
            'issues': issues,
            'recommendations': [
                'Apply scaling factors in validation script',
                'Run calibration to match UNAIDS data',
                'Consider full-scale simulation for final validation'
            ]
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Full diagnostic report saved: {report_path}")


def main():
    parser = argparse.ArgumentParser(description='Diagnose model configuration issues')
    parser.add_argument('--show-conversions', action='store_true', 
                       help='Show detailed conversion formulas')
    
    args = parser.parse_args()
    
    diagnostic = ModelDiagnostic()
    
    print("\n" + "="*60)
    print("HIVEC-CM MODEL CONFIGURATION DIAGNOSTIC")
    print("="*60)
    
    # Run diagnostics
    model_pop = diagnostic.check_population_size()
    df = diagnostic.check_output_units()
    scaling_factors = diagnostic.calculate_scaling_factors(model_pop)
    diagnostic.check_transmission_parameters()
    diagnostic.recommend_fixes(scaling_factors)
    diagnostic.generate_summary_report(model_pop, scaling_factors)
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Run: python fix_validation_scaling.py")
    print("2. Run: python calibrate_model.py")
    print("3. Run: python quick_validate.py --period both")
    print("4. Run: python generate_diagnostics.py")


if __name__ == '__main__':
    main()
