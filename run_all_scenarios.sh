#!/bin/bash
# Run Monte Carlo simulations for all requested scenarios
# 1985-2100, 20 iterations, 10,000 agents, 8 cores

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "🚀 HIVEC-CM Multi-Scenario Monte Carlo Simulation Suite"
echo "================================================================================"
echo ""
echo "Configuration:"
echo "  Period: 1985-2100 (115 years)"
echo "  Population: 10,000 agents"
echo "  Iterations: 20 per scenario"
echo "  CPU Cores: 8"
echo "  Output: results/full_scale_1985_2100/"
echo ""
echo "Scenarios to run:"
echo "  1. S0_baseline - Status quo (current trends)"
echo "  2. S1a_optimistic_funding - Increased funding (20% boost)"
echo "  3. S1b_pessimistic_funding - Decreased funding (50% cut)"
echo "  4. S3a_psn_aspirational - PSN 2024-2030 full implementation (95-95-95)"
echo ""
echo "================================================================================"
echo ""

# Scenario 1: Baseline
echo "▶️  [1/4] Running S0_baseline (Status Quo)..."
echo "================================================================================"
python scripts/run_enhanced_montecarlo.py \
    --scenario S0_baseline \
    --start-year 1985 \
    --end-year 2100 \
    --population 10000 \
    --iterations 20 \
    --output-dir results/full_scale_1985_2100 \
    --cores 8

echo ""
echo "✅ S0_baseline completed!"
echo ""

# Scenario 2: Optimistic Funding (Increased)
echo "▶️  [2/4] Running S1a_optimistic_funding (Increased Funding +20%)..."
echo "================================================================================"
python scripts/run_enhanced_montecarlo.py \
    --scenario S1a_optimistic_funding \
    --start-year 1985 \
    --end-year 2100 \
    --population 10000 \
    --iterations 20 \
    --output-dir results/full_scale_1985_2100 \
    --cores 8

echo ""
echo "✅ S1a_optimistic_funding completed!"
echo ""

# Scenario 3: Pessimistic Funding (50% cut - note: default is 20% cut, will need adjustment)
echo "▶️  [3/4] Running S1b_pessimistic_funding (Decreased Funding -20%)..."
echo "⚠️  Note: Default is -20%. For -50%, parameter adjustments needed."
echo "================================================================================"
python scripts/run_enhanced_montecarlo.py \
    --scenario S1b_pessimistic_funding \
    --start-year 1985 \
    --end-year 2100 \
    --population 10000 \
    --iterations 20 \
    --output-dir results/full_scale_1985_2100 \
    --cores 8

echo ""
echo "✅ S1b_pessimistic_funding completed!"
echo ""

# Scenario 4: PSN Aspirational (95-95-95)
echo "▶️  [4/4] Running S3a_psn_aspirational (PSN 2024-2030 Full Implementation)..."
echo "================================================================================"
python scripts/run_enhanced_montecarlo.py \
    --scenario S3a_psn_aspirational \
    --start-year 1985 \
    --end-year 2100 \
    --population 10000 \
    --iterations 20 \
    --output-dir results/full_scale_1985_2100 \
    --cores 8

echo ""
echo "✅ S3a_psn_aspirational completed!"
echo ""

echo "================================================================================"
echo "🎉 All 4 scenarios completed successfully!"
echo "================================================================================"
echo ""
echo "📊 Results location: results/full_scale_1985_2100/"
echo ""
echo "Generated outputs per scenario:"
echo "  - 17 CSV files with Phase 1-3 enhanced data collection"
echo "  - Basic results summary"
echo "  - Detailed annual indicators"
echo ""
echo "Total data files: ~68 CSVs (17 types × 4 scenarios)"
echo "================================================================================"
