"""
Real-time simulation monitor for HIVEC-CM
Tracks simulation progress and displays live statistics
"""
import json
import time
from pathlib import Path
from typing import Dict, Optional
import pandas as pd


class SimulationMonitor:
    """Monitor and track simulation progress in real-time."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.progress_file = self.output_dir / ".progress.json"
        self.live_data_file = self.output_dir / ".live_data.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def update_progress(self, 
                       scenario: str,
                       scenario_num: int,
                       total_scenarios: int,
                       current_year: float,
                       start_year: float,
                       end_year: float,
                       agents_alive: int,
                       agents_hiv_positive: int,
                       agents_on_art: int,
                       new_infections: int):
        """Update progress data for live monitoring."""
        
        year_progress = (current_year - start_year) / (end_year - start_year)
        overall_progress = ((scenario_num - 1) + year_progress) / total_scenarios
        
        progress_data = {
            'timestamp': time.time(),
            'scenario': scenario,
            'scenario_num': scenario_num,
            'total_scenarios': total_scenarios,
            'current_year': current_year,
            'start_year': start_year,
            'end_year': end_year,
            'year_progress': year_progress * 100,
            'overall_progress': overall_progress * 100,
            'agents_alive': agents_alive,
            'agents_hiv_positive': agents_hiv_positive,
            'agents_on_art': agents_on_art,
            'new_infections_this_year': new_infections,
            'prevalence': (agents_hiv_positive / agents_alive * 100) if agents_alive > 0 else 0,
            'art_coverage': (agents_on_art / agents_hiv_positive * 100) if agents_hiv_positive > 0 else 0
        }
        
        # Write progress file (overwrite)
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
        
        # Append to live data log
        with open(self.live_data_file, 'a') as f:
            f.write(json.dumps(progress_data) + '\n')
    
    def read_progress(self) -> Optional[Dict]:
        """Read current progress data."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def read_live_data(self) -> pd.DataFrame:
        """Read all live data as DataFrame."""
        if not self.live_data_file.exists():
            return pd.DataFrame()
        
        data = []
        with open(self.live_data_file, 'r') as f:
            for line in f:
                try:
                    data.append(json.loads(line.strip()))
                except:
                    continue
        
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    def mark_scenario_complete(self, scenario: str):
        """Mark a scenario as complete."""
        progress = self.read_progress()
        if progress:
            progress['scenario_complete'] = scenario
            progress['timestamp'] = time.time()
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
    
    def mark_all_complete(self):
        """Mark entire simulation run as complete."""
        progress = self.read_progress() or {}
        progress['all_complete'] = True
        progress['completion_time'] = time.time()
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def cleanup(self):
        """Clean up progress files after completion."""
        if self.progress_file.exists():
            self.progress_file.unlink()
        # Keep live_data_file for history