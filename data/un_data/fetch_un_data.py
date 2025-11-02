#!/usr/bin/env python3
"""
UN Population Data Portal - Data Extraction Script
===================================================
Fetches demographic and HIV indicators for Cameroon from UN Data Portal API.

Usage:
    python fetch_un_data.py --indicator all
    python fetch_un_data.py --indicator demographic
    python fetch_un_data.py --indicator hiv
    python fetch_un_data.py --indicator population_total --start 1990 --end 2023

Author: HIVEC-CM Model Team
Date: 2024
"""

import json
import requests
import pandas as pd
import argparse
from pathlib import Path
import time
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UNDataFetcher:
    """Fetches data from UN Population Data Portal API."""
    
    def __init__(self, config_path: str = "un_api_config.json"):
        """Initialize with API configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.base_url = self.config['api_endpoint']
        self.headers = {
            'Authorization': f"Bearer {self.config['bearer_token']}"
        }
        self.location_code = self.config['location']['cameroon']['code']
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def _load_config(self) -> Dict:
        """Load API configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def fetch_indicator(
        self, 
        indicator_code: int,
        start_year: int = 1990,
        end_year: int = 2023,
        sex: Optional[str] = None,
        age_group: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch data for a specific indicator.
        
        Parameters:
        -----------
        indicator_code : int
            UN indicator code
        start_year : int
            Start year for data extraction
        end_year : int
            End year for data extraction
        sex : str, optional
            'Male', 'Female', or 'Both'
        age_group : str, optional
            Age group specification (e.g., '15-19', '20-24')
            
        Returns:
        --------
        pd.DataFrame
            Extracted data
        """
        # Build API query
        url = f"{self.base_url}/data/indicators/{indicator_code}/locations/{self.location_code}/start/{start_year}/end/{end_year}"
        
        logger.info(f"Fetching indicator {indicator_code} for years {start_year}-{end_year}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data:
                logger.warning(f"No data returned for indicator {indicator_code}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(data['data'])
            
            # Filter by sex if specified
            if sex and 'sex' in df.columns:
                df = df[df['sex'] == sex]
            
            # Filter by age group if specified
            if age_group and 'ageLabel' in df.columns:
                df = df[df['ageLabel'] == age_group]
            
            logger.info(f"Retrieved {len(df)} records")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return pd.DataFrame()
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding failed: {e}")
            return pd.DataFrame()
    
    def fetch_demographic_indicators(
        self, 
        start_year: int = 1990, 
        end_year: int = 2023
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch all demographic indicators.
        
        Returns:
        --------
        dict
            Dictionary of indicator_name -> DataFrame
        """
        results = {}
        demographic_indicators = self.config['indicators']['demographic']
        
        for indicator_name, indicator_info in demographic_indicators.items():
            logger.info(f"Fetching {indicator_name}...")
            
            df = self.fetch_indicator(
                indicator_code=indicator_info['code'],
                start_year=start_year,
                end_year=end_year
            )
            
            if not df.empty:
                results[indicator_name] = df
                
                # Save to CSV
                output_path = Path("raw") / f"{indicator_name}.csv"
                output_path.parent.mkdir(exist_ok=True)
                df.to_csv(output_path, index=False)
                logger.info(f"Saved to {output_path}")
            
            # Rate limiting
            time.sleep(0.5)
        
        return results
    
    def fetch_hiv_indicators(
        self, 
        start_year: int = 1990, 
        end_year: int = 2023
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch all HIV indicators.
        
        Returns:
        --------
        dict
            Dictionary of indicator_name -> DataFrame
        """
        results = {}
        hiv_indicators = self.config['indicators']['hiv']
        
        for indicator_name, indicator_info in hiv_indicators.items():
            logger.info(f"Fetching {indicator_name}...")
            
            df = self.fetch_indicator(
                indicator_code=indicator_info['code'],
                start_year=start_year,
                end_year=end_year
            )
            
            if not df.empty:
                results[indicator_name] = df
                
                # Save to CSV
                output_path = Path("raw") / f"{indicator_name}.csv"
                output_path.parent.mkdir(exist_ok=True)
                df.to_csv(output_path, index=False)
                logger.info(f"Saved to {output_path}")
            
            # Rate limiting
            time.sleep(0.5)
        
        return results
    
    def fetch_age_sex_population(
        self, 
        start_year: int = 1990, 
        end_year: int = 2023
    ) -> pd.DataFrame:
        """
        Fetch population by age and sex with detailed stratification.
        
        Returns:
        --------
        pd.DataFrame
            Population data by year, age group, and sex
        """
        indicator_code = self.config['indicators']['demographic']['population_by_age_sex']['code']
        
        logger.info(f"Fetching age-sex stratified population data...")
        
        df = self.fetch_indicator(
            indicator_code=indicator_code,
            start_year=start_year,
            end_year=end_year
        )
        
        if not df.empty:
            # Pivot to wide format for easier analysis
            if 'ageLabel' in df.columns and 'sex' in df.columns:
                df_pivot = df.pivot_table(
                    index=['timeLabel', 'ageLabel'],
                    columns='sex',
                    values='value',
                    aggfunc='first'
                ).reset_index()
                
                # Save both formats
                output_path_long = Path("raw") / "population_age_sex_long.csv"
                output_path_wide = Path("raw") / "population_age_sex_wide.csv"
                
                df.to_csv(output_path_long, index=False)
                df_pivot.to_csv(output_path_wide, index=False)
                
                logger.info(f"Saved long format to {output_path_long}")
                logger.info(f"Saved wide format to {output_path_wide}")
                
                return df_pivot
        
        return df
    
    def create_validation_targets(self) -> None:
        """
        Create structured validation target files from raw UN data.
        
        Outputs JSON files with calibration and validation targets.
        """
        logger.info("Creating validation target files...")
        
        # Load configuration time periods
        calibration_period = self.config['time_period']['calibration']
        validation_period = self.config['time_period']['validation']
        
        validation_targets = {
            'metadata': {
                'source': 'UN Population Data Portal',
                'location': 'Cameroon',
                'location_code': self.location_code,
                'calibration_period': f"{calibration_period['start']}-{calibration_period['end']}",
                'validation_period': f"{validation_period['start']}-{validation_period['end']}",
                'extracted_date': time.strftime('%Y-%m-%d')
            },
            'calibration_targets': {},
            'validation_targets': {},
            'acceptance_criteria': self.config['validation_metrics']['acceptance_criteria']
        }
        
        # Process each indicator
        raw_dir = Path("raw")
        if raw_dir.exists():
            for csv_file in raw_dir.glob("*.csv"):
                indicator_name = csv_file.stem
                logger.info(f"Processing {indicator_name}...")
                
                try:
                    df = pd.read_csv(csv_file)
                    
                    if 'timeLabel' not in df.columns or 'value' not in df.columns:
                        logger.warning(f"Skipping {indicator_name}: missing required columns")
                        continue
                    
                    # Convert year to integer
                    df['year'] = pd.to_numeric(df['timeLabel'], errors='coerce')
                    df = df.dropna(subset=['year', 'value'])
                    df['year'] = df['year'].astype(int)
                    
                    # Split into calibration and validation
                    df_calib = df[
                        (df['year'] >= calibration_period['start']) & 
                        (df['year'] <= calibration_period['end'])
                    ]
                    
                    df_valid = df[
                        (df['year'] >= validation_period['start']) & 
                        (df['year'] <= validation_period['end'])
                    ]
                    
                    # Store as year -> value mappings
                    if not df_calib.empty:
                        validation_targets['calibration_targets'][indicator_name] = {
                            int(row['year']): float(row['value']) 
                            for _, row in df_calib.iterrows()
                        }
                    
                    if not df_valid.empty:
                        validation_targets['validation_targets'][indicator_name] = {
                            int(row['year']): float(row['value']) 
                            for _, row in df_valid.iterrows()
                        }
                    
                except Exception as e:
                    logger.error(f"Error processing {indicator_name}: {e}")
        
        # Save validation targets
        output_path = Path("../validation_targets") / "un_validation_targets.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(validation_targets, f, indent=2)
        
        logger.info(f"Validation targets saved to {output_path}")
        
        # Print summary
        n_calib = len(validation_targets['calibration_targets'])
        n_valid = len(validation_targets['validation_targets'])
        logger.info(f"Created {n_calib} calibration targets and {n_valid} validation targets")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Fetch data from UN Population Data Portal'
    )
    parser.add_argument(
        '--indicator',
        type=str,
        default='all',
        choices=['all', 'demographic', 'hiv', 'population_total', 'population_age_sex', 
                 'births', 'deaths', 'fertility', 'life_expectancy', 'hiv_prevalence'],
        help='Indicator category or specific indicator to fetch'
    )
    parser.add_argument(
        '--start',
        type=int,
        default=1990,
        help='Start year for data extraction'
    )
    parser.add_argument(
        '--end',
        type=int,
        default=2023,
        help='End year for data extraction'
    )
    parser.add_argument(
        '--create-targets',
        action='store_true',
        help='Create validation target files after fetching data'
    )
    
    args = parser.parse_args()
    
    # Initialize fetcher
    fetcher = UNDataFetcher()
    
    # Fetch data based on indicator selection
    if args.indicator == 'all':
        logger.info("Fetching all indicators...")
        fetcher.fetch_demographic_indicators(args.start, args.end)
        fetcher.fetch_hiv_indicators(args.start, args.end)
        fetcher.fetch_age_sex_population(args.start, args.end)
        
    elif args.indicator == 'demographic':
        fetcher.fetch_demographic_indicators(args.start, args.end)
        
    elif args.indicator == 'hiv':
        fetcher.fetch_hiv_indicators(args.start, args.end)
        
    elif args.indicator == 'population_age_sex':
        fetcher.fetch_age_sex_population(args.start, args.end)
        
    else:
        # Fetch specific indicator
        indicator_code = None
        for category in ['demographic', 'hiv']:
            indicators = fetcher.config['indicators'][category]
            for name, info in indicators.items():
                if name == args.indicator:
                    indicator_code = info['code']
                    break
            if indicator_code:
                break
        
        if indicator_code:
            df = fetcher.fetch_indicator(indicator_code, args.start, args.end)
            if not df.empty:
                output_path = Path("raw") / f"{args.indicator}.csv"
                output_path.parent.mkdir(exist_ok=True)
                df.to_csv(output_path, index=False)
                logger.info(f"Saved to {output_path}")
        else:
            logger.error(f"Unknown indicator: {args.indicator}")
    
    # Create validation targets if requested
    if args.create_targets:
        fetcher.create_validation_targets()
    
    logger.info("Data extraction complete!")


if __name__ == '__main__':
    main()
