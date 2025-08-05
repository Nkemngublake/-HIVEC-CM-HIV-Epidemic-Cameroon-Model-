"""
Utility modules for HIV/AIDS Epidemiological Model
================================================

Data loading, configuration management, and helper utilities.
"""

import pandas as pd
import numpy as np
import yaml
import json
import os
import logging
from typing import Dict, Any, Optional


class DataLoader:
    """Handles loading and preprocessing of HIV/AIDS data for Cameroon."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Default to data directory relative to project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            data_dir = os.path.join(project_root, 'data')
        self.data_dir = data_dir
    
    def load_cameroon_data(self, custom_file: str = None) -> pd.DataFrame:
        """Load integrated Cameroon HIV/AIDS data."""
        if custom_file and os.path.exists(custom_file):
            data_file = custom_file
        else:
            data_file = os.path.join(self.data_dir, 'cameroon_hiv_population_data.csv')
        
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Data file not found: {data_file}")
        
        # Load and validate data
        data = pd.read_csv(data_file)
        required_columns = ['Year', 'HIV_Prevalence_Rate', 'Population_Total']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Clean and preprocess
        data = data.dropna(subset=required_columns)
        data['Year'] = pd.to_numeric(data['Year'], errors='coerce')
        data['HIV_Prevalence_Rate'] = pd.to_numeric(data['HIV_Prevalence_Rate'], errors='coerce')
        data['Population_Total'] = pd.to_numeric(data['Population_Total'], errors='coerce')
        
        # Remove any rows with invalid data
        data = data.dropna()
        
        # Sort by year
        data = data.sort_values('Year').reset_index(drop=True)
        
        logging.info(f"Loaded {len(data)} data points from {data['Year'].min()} to {data['Year'].max()}")
        
        return data
    
    def validate_data(self, data: pd.DataFrame = None, file_path: str = None) -> bool:
        """Validate data integrity and completeness."""
        if data is None:
            data = self.load_cameroon_data(file_path)
        
        validation_results = {
            'total_records': len(data),
            'year_range': (data['Year'].min(), data['Year'].max()),
            'missing_values': data.isnull().sum().to_dict(),
            'prevalence_range': (data['HIV_Prevalence_Rate'].min(), data['HIV_Prevalence_Rate'].max()),
            'population_range': (data['Population_Total'].min(), data['Population_Total'].max())
        }
        
        # Validation checks
        issues = []
        
        if len(data) < 10:
            issues.append(f"Insufficient data points: {len(data)}")
        
        if data['HIV_Prevalence_Rate'].max() > 20 or data['HIV_Prevalence_Rate'].min() < 0:
            issues.append("HIV prevalence outside expected range (0-20%)")
        
        if data['Population_Total'].min() <= 0:
            issues.append("Invalid population values found")
        
        if data.isnull().sum().sum() > 0:
            issues.append("Missing values detected")
        
        if issues:
            logging.warning(f"Data validation issues: {'; '.join(issues)}")
            return False
        else:
            logging.info("Data validation passed")
            return True


class ConfigManager:
    """Manages configuration files and parameter settings."""
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration parameters."""
        return {
            'model': {
                'initial_population': 75000,
                'initial_hiv_prevalence': 0.054,
                'initial_art_coverage': 0.1,
                'transmission_rate': 0.12,
                'recovery_rate': 0.0,
                'death_rate_hiv': 0.05,
                'death_rate_natural': 0.011,
                'birth_rate': 0.032,
                'art_efficacy': 0.95,
                'art_failure_rate': 0.02,
                'preexposure_prophylaxis_efficacy': 0.9,
                'male_circumcision_efficacy': 0.6,
                'hiv_test_sensitivity': 0.99,
                'hiv_test_specificity': 0.995
            },
            'simulation': {
                'years': 35,
                'dt': 0.1,
                'output_frequency': 10
            },
            'calibration': {
                'method': 'differential_evolution',
                'max_iterations': 100,
                'tolerance': 1e-6,
                'parameters_to_calibrate': [
                    'transmission_rate',
                    'death_rate_hiv',
                    'art_efficacy'
                ]
            },
            'analysis': {
                'generate_plots': True,
                'save_detailed_output': True,
                'validation_enabled': True
            },
            'interventions': {
                'art_scale_up': {
                    'enabled': True,
                    'start_year': 2005,
                    'target_coverage': 0.81,
                    'scale_up_rate': 0.1
                },
                'prevention_programs': {
                    'enabled': True,
                    'start_year': 2010,
                    'effectiveness': 0.3
                },
                'male_circumcision': {
                    'enabled': True,
                    'start_year': 2008,
                    'coverage': 0.6
                }
            }
        }
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logging.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            raise
    
    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str) -> None:
        """Save configuration to YAML file."""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            logging.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            raise
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """Validate configuration parameters."""
        required_sections = ['model', 'simulation']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate model parameters
        model_params = config['model']
        if model_params.get('initial_population', 0) <= 0:
            raise ValueError("initial_population must be positive")
        
        if not 0 <= model_params.get('initial_hiv_prevalence', 0) <= 1:
            raise ValueError("initial_hiv_prevalence must be between 0 and 1")
        
        # Validate simulation parameters
        sim_params = config['simulation']
        if sim_params.get('years', 0) <= 0:
            raise ValueError("simulation years must be positive")
        
        if sim_params.get('dt', 0) <= 0:
            raise ValueError("simulation dt must be positive")
        
        return True


def load_cameroon_data(custom_file: str = None) -> pd.DataFrame:
    """Convenience function to load Cameroon data."""
    loader = DataLoader()
    return loader.load_cameroon_data(custom_file)


def validate_data(file_path: str = None) -> bool:
    """Convenience function to validate data."""
    loader = DataLoader()
    return loader.validate_data(file_path=file_path)


def create_results_structure(output_dir: str) -> None:
    """Create standardized results directory structure."""
    subdirs = [
        'simulation',
        'analysis',
        'plots',
        'calibration',
        'config'
    ]
    
    for subdir in subdirs:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
    
    logging.info(f"Results directory structure created: {output_dir}")


def format_parameter_summary(params) -> str:
    """Format model parameters for display."""
    if hasattr(params, '__dict__'):
        param_dict = vars(params)
    else:
        param_dict = params
    
    summary = "Model Parameters Summary:\n"
    summary += "-" * 30 + "\n"
    
    for key, value in param_dict.items():
        if isinstance(value, float):
            summary += f"{key:25}: {value:.4f}\n"
        else:
            summary += f"{key:25}: {value}\n"
    
    return summary


def calculate_epidemiological_metrics(data: pd.DataFrame) -> Dict[str, float]:
    """Calculate basic epidemiological metrics from data."""
    metrics = {}
    
    if 'HIV_Prevalence_Rate' in data.columns:
        prevalence = data['HIV_Prevalence_Rate']
        metrics['mean_prevalence'] = prevalence.mean()
        metrics['max_prevalence'] = prevalence.max()
        metrics['min_prevalence'] = prevalence.min()
        metrics['std_prevalence'] = prevalence.std()
    
    if 'Population_Total' in data.columns:
        population = data['Population_Total']
        metrics['mean_population'] = population.mean()
        metrics['population_growth_rate'] = (population.iloc[-1] / population.iloc[0]) ** (1/len(population)) - 1
    
    if len(data) > 1 and 'Year' in data.columns:
        metrics['data_span_years'] = data['Year'].max() - data['Year'].min()
        metrics['data_points'] = len(data)
    
    return metrics
