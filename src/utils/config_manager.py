"""
Configuration management for HIV/AIDS model
"""

import yaml
import os
import logging


class ConfigManager:
    """Manages configuration files and parameter settings."""
    
    @staticmethod
    def get_default_config():
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
            }
        }
    
    @staticmethod
    def load_config(config_path):
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
    def save_config(config, config_path):
        """Save configuration to YAML file."""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            logging.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            raise
