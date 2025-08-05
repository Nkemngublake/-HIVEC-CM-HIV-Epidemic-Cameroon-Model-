"""
Simple data loading utilities for HIV/AIDS model
"""

import pandas as pd
import os
import logging


def load_cameroon_data(custom_file=None):
    """Load integrated Cameroon HIV/AIDS data."""
    if custom_file and os.path.exists(custom_file):
        data_file = custom_file
    else:
        # Get project root directory
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(os.path.dirname(current_dir))
        data_file = os.path.join(project_root, 'data', 
                                'cameroon_hiv_population_data.csv')
    
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    # Load and validate data
    data = pd.read_csv(data_file)
    required_columns = ['Year', 'HIV_Prevalence_Rate', 'Population_Total']
    missing_columns = [col for col in required_columns 
                      if col not in data.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Clean and preprocess
    data = data.dropna(subset=required_columns)
    data['Year'] = pd.to_numeric(data['Year'], errors='coerce')
    data['HIV_Prevalence_Rate'] = pd.to_numeric(
        data['HIV_Prevalence_Rate'], errors='coerce')
    data['Population_Total'] = pd.to_numeric(
        data['Population_Total'], errors='coerce')
    
    # Remove any rows with invalid data
    data = data.dropna()
    
    # Sort by year
    data = data.sort_values('Year').reset_index(drop=True)
    
    logging.info(f"Loaded {len(data)} data points from "
                f"{data['Year'].min()} to {data['Year'].max()}")
    
    return data


def validate_data(file_path=None):
    """Validate data integrity and completeness."""
    try:
        data = load_cameroon_data(file_path)
    except Exception as e:
        logging.error(f"Data validation failed: {e}")
        return False
    
    # Validation checks
    issues = []
    
    if len(data) < 10:
        issues.append(f"Insufficient data points: {len(data)}")
    
    prevalence_range = data['HIV_Prevalence_Rate']
    if prevalence_range.max() > 20 or prevalence_range.min() < 0:
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
