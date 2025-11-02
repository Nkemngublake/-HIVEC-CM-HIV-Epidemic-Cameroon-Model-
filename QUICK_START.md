# Quick Reference - New Project Structure

## 🚀 Quick Commands

### Docker Deployment
```bash
# Start UI (from project root)
./docker/start_ui.sh

# Manual commands
docker-compose -f docker/docker-compose.yml up -d --build    # Build & start
docker-compose -f docker/docker-compose.yml logs -f          # View logs
docker-compose -f docker/docker-compose.yml down             # Stop
```

### Run Simulations
```bash
# All scenarios
python scripts/run_all_scenarios.py --start-year 1985 --years 115 --population 10000

# Via web UI
open http://localhost:8501
```

## 📁 Where to Find Things

| What | Location |
|------|----------|
| **Docker files** | `docker/` |
| **Documentation** | `docs/` (organized by category) |
| **Configuration** | `config/parameters.json` |
| **Run scripts** | `scripts/run_all_scenarios.py` |
| **Results** | `results/` |
| **Web interface** | `ui/app.py` |
| **Source code** | `src/hivec_cm/` |

## 📚 Documentation Categories

```
docs/
├── 01_calibration/         ← Parameters & calibration
├── 02_validation/          ← Model validation
├── 03_data_collection/     ← Enhanced data features
├── 04_scenarios/           ← Policy scenarios
├── 05_integration/         ← CAMPHIA & demographics
├── 07_quick_references/    ← Quick guides (start here!)
├── 08_session_summaries/   ← Development history
├── 09_technical/           ← Technical specs
└── 10_analysis/            ← Analysis guides
```

## 🎯 Common Tasks

### View Recent Results
```bash
ls -lt results/ | head
# or use web UI at http://localhost:8501
```

### Check Simulation Status
```bash
ps aux | grep run_all_scenarios
# or check results folder for execution_summary.json
```

### Read Documentation
```bash
# Quick references (start here)
ls docs/07_quick_references/

# Scenario info
cat docs/04_scenarios/SCENARIO_QUICK_REFERENCE.md

# Project structure
cat docs/PROJECT_STRUCTURE.md
```

### Configure Parameters
```bash
# Edit main config
nano config/parameters.json

# Or use web UI parameter editor
open http://localhost:8501
```

## 🔧 Troubleshooting

### Docker Issues
```bash
# See logs
docker-compose -f docker/docker-compose.yml logs

# Rebuild clean
./docker/start_ui.sh
# Select option 5 (Rebuild from scratch)
```

### Find Specific Documentation
```bash
# Search all docs
grep -r "keyword" docs/

# List by category
ls docs/04_scenarios/
ls docs/07_quick_references/
```

## 📖 Important Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `docker/README.md` | Docker deployment guide |
| `docs/PROJECT_STRUCTURE.md` | Complete file reference |
| `docs/REORGANIZATION_SUMMARY.md` | What changed & why |
| `docs/07_quick_references/` | Quick start guides |
| `config/parameters.json` | Current model parameters |

## 🎨 What Changed (Nov 2025)

✅ **Docker files** → Moved to `docker/` folder  
✅ **30+ MD files** → Organized into `docs/` categories  
✅ **Root directory** → Clean and professional  
✅ **New guides** → docker/README.md, PROJECT_STRUCTURE.md  

**Nothing broke!** All paths updated, functionality preserved.

---

**Need help?** Check `docs/PROJECT_STRUCTURE.md` for complete reference!
