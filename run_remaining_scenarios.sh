#!/bin/bash
# Run remaining Monte Carlo scenarios (S1a, S1b, S3a)
# S0_baseline already completed successfully

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "🚀 HIVEC-CM Remaining Scenarios - Monte Carlo Simulation"
echo "================================================================================"
echo ""
echo "Configuration:"
echo "  Period: 1985-2100 (115 years)"
echo "  Population: 10,000 agents"
echo "  Iterations: 20 per scenario"
echo "  CPU Cores: 8"
echo "  Output: results/full_scale_1985_2100/"
echo ""
echo "Remaining scenarios:"
echo "  ✅ S0_baseline - Already completed"
echo "  🔄 S1a_optimistic_funding - Increased funding (+20%)"
echo "  ⏳ S1b_pessimistic_funding - Decreased funding (-20%)"
echo "  ⏳ S3a_psn_aspirational - PSN 2024-2030 full implementation (95-95-95)"
echo ""
echo "================================================================================"
echo ""

# Check if S1a is already running
if pgrep -f "S1a_optimistic_funding" > /dev/null; then
    echo "⚠️  S1a_optimistic_funding is already running. Waiting for completion..."
    echo "   (You can monitor progress in the other terminal)"
    echo ""
    while pgrep -f "S1a_optimistic_funding" > /dev/null; do
        sleep 30
    done
    echo "✅ S1a_optimistic_funding completed!"
    echo ""
else
    # Scenario 1: Optimistic Funding
    echo "▶️  [1/3] Running S1a_optimistic_funding (Increased Funding +20%)..."
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
fi

# Scenario 2: Pessimistic Funding (-20%)
echo "▶️  [2/3] Running S1b_pessimistic_funding (Decreased Funding -20%)..."
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

# Scenario 3: PSN Aspirational (95-95-95)
echo "▶️  [3/3] Running S3a_psn_aspirational (PSN 2024-2030 Full Implementation)..."
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
echo "🎉 All scenarios completed successfully!"
echo "================================================================================"
echo ""
echo "📊 Completed simulations:"
echo "   ✅ S0_baseline (Status Quo)"
echo "   ✅ S1a_optimistic_funding (Increased Funding)"
echo "   ✅ S1b_pessimistic_funding (Decreased Funding)"
echo "   ✅ S3a_psn_aspirational (PSN Aspirational)"
echo ""
echo "📂 Results location: results/full_scale_1985_2100/"
echo ""
echo "📊 Output structure per scenario:"
echo "   - 17 CSV files with enhanced data (Phases 1-3)"
echo "   - Basic results summary"
echo "   - Detailed annual indicators"
echo ""
echo "Total generated files: ~68 CSVs (17 types × 4 scenarios)"
echo ""
echo "📈 Next steps:"
echo "   1. Verify all outputs in results/full_scale_1985_2100/"
echo "   2. Run comparative analysis across scenarios"
echo "   3. Generate publication-quality plots"
echo "   4. Calculate policy impact metrics"
echo ""
echo "================================================================================"
