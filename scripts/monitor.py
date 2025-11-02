#!/usr/bin/env python3
"""
HIVEC-CM Monitoring Tool
Real-time monitoring of running simulations:
  - Live progress tracking
  - Scenario status updates
  - Performance metrics
  - Results monitoring
  
Consolidates: monitor_saint_seya.py, monitor_simulation.py
"""

import argparse
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path


def monitor_simulation(results_dir, interval=5):
    """Monitor a running simulation with live updates."""
    print("=" * 80)
    print("HIVEC-CM SIMULATION MONITOR")
    print("=" * 80)
    print(f"Monitoring: {results_dir}")
    print(f"Refresh interval: {interval} seconds")
    print(f"Press Ctrl+C to stop\n")
    
    last_year = None
    start_time = time.time()
    
    try:
        while True:
            # Clear screen (works on Unix/Mac)
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("=" * 80)
            print("HIVEC-CM SIMULATION MONITOR")
            print("=" * 80)
            elapsed = time.time() - start_time
            print(f"Elapsed time: {elapsed:.1f}s")
            print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Check for results file
            json_file = os.path.join(results_dir, 'detailed_results.json')
            csv_file = os.path.join(results_dir, 'results.csv')
            
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    years = sorted(data.keys())
                    if len(years) > 0:
                        current_year = years[-1]
                        year_data = data[current_year]
                        
                        print("📊 SIMULATION PROGRESS:")
                        print("-" * 80)
                        print(f"  Current year: {current_year}")
                        print(f"  Years completed: {len(years)}")
                        
                        if last_year and current_year != last_year:
                            rate = 1.0 / interval
                            print(f"  Progress rate: {rate:.2f} years/second")
                        
                        # Show key metrics
                        agg = year_data.get('aggregate', {})
                        print(f"\n  Population: {agg.get('population', 0):,.0f}")
                        print(f"  Infected: {agg.get('infected', 0):,.0f}")
                        print(f"  Prevalence: {agg.get('prevalence', 0):.2%}")
                        print(f"  On ART: {agg.get('on_art', 0):,.0f}")
                        print(f"  New infections: {agg.get('new_infections', 0):,.0f}")
                        
                        # Treatment cascade
                        cascade = year_data.get('treatment_cascade_95_95_95', {})
                        if cascade:
                            print(f"\n  95-95-95 Cascade:")
                            print(f"    Diagnosed: {cascade.get('diagnosed_coverage', 0):.1%}")
                            print(f"    On ART: {cascade.get('on_art_coverage', 0):.1%}")
                            print(f"    Suppressed: {cascade.get('virally_suppressed_coverage', 0):.1%}")
                        
                        last_year = current_year
                
                except json.JSONDecodeError:
                    print("⚠️  Results file is being written...")
                except Exception as e:
                    print(f"⚠️  Error reading results: {e}")
            
            elif os.path.exists(csv_file):
                print("📊 SIMULATION IN PROGRESS")
                print("-" * 80)
                print("  Found results.csv (basic format)")
                print("  Detailed JSON not yet available")
            
            else:
                print("⏳ WAITING FOR SIMULATION TO START")
                print("-" * 80)
                print("  No results files found yet")
            
            print("\n" + "=" * 80)
            print("Press Ctrl+C to stop monitoring")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped by user")
        return 0


def monitor_scenarios(base_dir, interval=10):
    """Monitor multiple scenario simulations."""
    print("=" * 80)
    print("HIVEC-CM SCENARIO MONITOR")
    print("=" * 80)
    print(f"Monitoring: {base_dir}")
    print(f"Refresh interval: {interval} seconds")
    print("Press Ctrl+C to stop\n")
    
    start_time = time.time()
    
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("=" * 80)
            print("HIVEC-CM SCENARIO MONITOR")
            print("=" * 80)
            elapsed = time.time() - start_time
            print(f"Elapsed: {elapsed:.1f}s")
            print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Find scenario directories
            scenario_dirs = [d for d in os.listdir(base_dir)
                           if os.path.isdir(os.path.join(base_dir, d))
                           and not d.startswith('_')]
            
            if len(scenario_dirs) == 0:
                print("⏳ WAITING FOR SCENARIOS")
                print("-" * 80)
                print("  No scenario directories found yet")
            else:
                print(f"📊 SCENARIO PROGRESS ({len(scenario_dirs)} scenarios):")
                print("=" * 80)
                
                scenario_status = []
                
                for scenario_id in sorted(scenario_dirs):
                    scenario_path = os.path.join(base_dir, scenario_id)
                    json_file = os.path.join(scenario_path, 'detailed_results.json')
                    
                    status = {
                        'id': scenario_id,
                        'status': 'Not started',
                        'years': 0,
                        'prevalence': 0,
                        'complete': False
                    }
                    
                    if os.path.exists(json_file):
                        try:
                            with open(json_file, 'r') as f:
                                data = json.load(f)
                            
                            years = sorted(data.keys())
                            status['years'] = len(years)
                            status['status'] = 'In progress'
                            
                            if len(years) > 0:
                                final = data[years[-1]]
                                agg = final.get('aggregate', {})
                                status['prevalence'] = agg.get('prevalence', 0)
                            
                            # Check if complete (metadata exists)
                            meta_file = os.path.join(scenario_path, 'run_metadata.json')
                            if os.path.exists(meta_file):
                                status['status'] = 'Complete'
                                status['complete'] = True
                        
                        except Exception:
                            status['status'] = 'Writing...'
                    
                    scenario_status.append(status)
                
                # Display table
                print(f"{'Scenario':<30} {'Status':<15} {'Years':<10} {'Prevalence'}")
                print("-" * 80)
                
                for s in scenario_status:
                    status_icon = "✓" if s['complete'] else "⏳"
                    prev_str = f"{s['prevalence']:.2%}" if s['prevalence'] > 0 else "-"
                    print(f"{status_icon} {s['id']:<28} {s['status']:<15} "
                          f"{s['years']:<10} {prev_str}")
                
                # Summary
                completed = sum(1 for s in scenario_status if s['complete'])
                in_progress = sum(1 for s in scenario_status 
                                if s['status'] == 'In progress')
                
                print("\n" + "-" * 80)
                print(f"Summary: {completed} completed, {in_progress} in progress, "
                      f"{len(scenario_status) - completed - in_progress} pending")
            
            print("\n" + "=" * 80)
            print("Press Ctrl+C to stop monitoring")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped by user")
        return 0


def quick_status(results_dir):
    """Quick status check (no continuous monitoring)."""
    print("=" * 80)
    print("SIMULATION STATUS CHECK")
    print("=" * 80)
    print(f"Directory: {results_dir}\n")
    
    # Check for results
    json_file = os.path.join(results_dir, 'detailed_results.json')
    csv_file = os.path.join(results_dir, 'results.csv')
    meta_file = os.path.join(results_dir, 'run_metadata.json')
    
    if os.path.exists(meta_file):
        with open(meta_file, 'r') as f:
            metadata = json.load(f)
        
        print("✓ SIMULATION COMPLETE")
        print("-" * 80)
        print(f"  Scenario: {metadata.get('scenario_id', 'Unknown')}")
        print(f"  Completed: {metadata.get('execution_time', 'Unknown')}")
        print(f"  Years: {metadata.get('years_simulated', 'Unknown')}")
        print(f"  Version: {metadata.get('model_version', 'Unknown')}")
        
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            final_year = sorted(data.keys())[-1]
            final_data = data[final_year]
            agg = final_data.get('aggregate', {})
            
            print(f"\n  Final Year ({final_year}):")
            print(f"    Population: {agg.get('population', 0):,.0f}")
            print(f"    Prevalence: {agg.get('prevalence', 0):.2%}")
            print(f"    Infected: {agg.get('infected', 0):,.0f}")
    
    elif os.path.exists(json_file):
        print("⏳ SIMULATION IN PROGRESS")
        print("-" * 80)
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            years = sorted(data.keys())
            print(f"  Years completed: {len(years)}")
            
            if len(years) > 0:
                current = data[years[-1]]
                agg = current.get('aggregate', {})
                print(f"  Current year: {years[-1]}")
                print(f"  Current prevalence: {agg.get('prevalence', 0):.2%}")
        
        except Exception as e:
            print(f"  ⚠️  Could not read data: {e}")
    
    elif os.path.exists(csv_file):
        print("⏳ SIMULATION STARTED")
        print("-" * 80)
        print("  Basic results file found")
        print("  Detailed data not yet available")
    
    else:
        print("⚠️  NO RESULTS FOUND")
        print("-" * 80)
        print("  Simulation may not have started")
    
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='HIVEC-CM Monitoring Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor single simulation (live updates every 5 seconds)
  %(prog)s --mode live --dir results/simulation_20251101_153959
  
  # Monitor multiple scenarios (live updates every 10 seconds)
  %(prog)s --mode scenarios --dir results/scenarios_20251101 --interval 10
  
  # Quick status check (no continuous monitoring)
  %(prog)s --mode status --dir results/simulation_20251101_153959
        """
    )
    
    parser.add_argument('--mode', type=str, required=True,
                       choices=['live', 'scenarios', 'status'],
                       help='Monitoring mode')
    
    parser.add_argument('--dir', type=str, required=True,
                       help='Results directory to monitor')
    
    parser.add_argument('--interval', type=int, default=5,
                       help='Refresh interval in seconds (default: 5)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print(f"❌ Directory not found: {args.dir}")
        return 1
    
    # Execute based on mode
    if args.mode == 'live':
        return monitor_simulation(args.dir, args.interval)
    elif args.mode == 'scenarios':
        return monitor_scenarios(args.dir, args.interval)
    elif args.mode == 'status':
        quick_status(args.dir)
        return 0


if __name__ == '__main__':
    sys.exit(main())
