PY ?= python3
TEX ?= pdflatex
# Optional: use Tectonic for reliable LaTeX builds
TECTONIC ?= tectonic
HAVE_TECTONIC := $(shell command -v $(TECTONIC) >/dev/null 2>&1 && echo yes || echo no)
ENTR ?= entr
HAVE_ENTR := $(shell command -v $(ENTR) >/dev/null 2>&1 && echo yes || echo no)

# Auto-detect latest study dir if not provided
STUDY_DIR ?= $(shell ls -td results/montecarlo_study/study_* 2>/dev/null | head -1)
MANUSCRIPTS_DIR ?= manuscripts

# Milestone thresholds (can be overridden)
INCIDENCE_THRESHOLD ?= 1.0
INCIDENCE_SCALE ?= per1000
PREVALENCE_THRESHOLD ?= 2.0
ART_THRESHOLD ?= 90.0

.PHONY: help labels methods calibration uncertainty fundingcut all report milestones clean

help:
	@echo "Targets:"
	@echo "  labels        Generate LaTeX macros (study_config.tex, labels.tex, fig_paths.tex)"
	@echo "  methods       Build Methods paper PDF"
	@echo "  calibration   Build Calibration/Validation paper PDF"
	@echo "  uncertainty   Build Uncertainty paper PDF"
	@echo "  fundingcut    Build Funding-cut Policy paper PDF"
	@echo "  all           Build labels + all four manuscripts"
	@echo "  milestones    Compute milestone years (incidence/prevalence/ART)"
	@echo "  report        Generate compact report.pdf from plots + labels"
	@echo "Variables (override as needed): STUDY_DIR, MANUSCRIPTS_DIR, TEX, PY"

labels:
	@test -n "$(STUDY_DIR)" || (echo "STUDY_DIR not set and no studies found in results/montecarlo_study" && exit 1)
	@mkdir -p $(MANUSCRIPTS_DIR)
	$(PY) scripts/generate_latex_labels.py --study-dir $(STUDY_DIR) --out-dir $(MANUSCRIPTS_DIR)

define build_latex
	@test -n "$(STUDY_DIR)" || (echo "STUDY_DIR not set and no studies found" && exit 1)
	$(TEX) -output-directory=$(MANUSCRIPTS_DIR) $(MANUSCRIPTS_DIR)/$1
endef

methods: labels
	@if [ "$(HAVE_TECTONIC)" = "yes" ]; then \
		cd $(MANUSCRIPTS_DIR) && $(TECTONIC) paper_methods.tex ; \
	else \
		$(TEX) -output-directory=$(MANUSCRIPTS_DIR) $(MANUSCRIPTS_DIR)/paper_methods.tex ; \
	fi

calibration: labels
	@if [ "$(HAVE_TECTONIC)" = "yes" ]; then \
		cd $(MANUSCRIPTS_DIR) && $(TECTONIC) paper_calibration.tex ; \
	else \
		$(TEX) -output-directory=$(MANUSCRIPTS_DIR) $(MANUSCRIPTS_DIR)/paper_calibration.tex ; \
	fi

uncertainty: labels
	@if [ "$(HAVE_TECTONIC)" = "yes" ]; then \
		cd $(MANUSCRIPTS_DIR) && $(TECTONIC) paper_uncertainty.tex ; \
	else \
		$(TEX) -output-directory=$(MANUSCRIPTS_DIR) $(MANUSCRIPTS_DIR)/paper_uncertainty.tex ; \
	fi

fundingcut: labels
	@if [ "$(HAVE_TECTONIC)" = "yes" ]; then \
		cd $(MANUSCRIPTS_DIR) && $(TECTONIC) paper_fundingcut.tex ; \
	else \
		$(TEX) -output-directory=$(MANUSCRIPTS_DIR) $(MANUSCRIPTS_DIR)/paper_fundingcut.tex ; \
	fi

all: labels methods calibration uncertainty fundingcut

milestones:
	@test -n "$(STUDY_DIR)" || (echo "STUDY_DIR not set and no studies found" && exit 1)
	$(PY) scripts/compute_milestones.py \
		--input-file $(STUDY_DIR)/montecarlo_results.csv \
		--output-dir $(STUDY_DIR)/analysis \
		--incidence-threshold $(INCIDENCE_THRESHOLD) \
		--incidence-scale $(INCIDENCE_SCALE) \
		--prevalence-threshold $(PREVALENCE_THRESHOLD) \
		--art-threshold $(ART_THRESHOLD)

report:
	@test -n "$(STUDY_DIR)" || (echo "STUDY_DIR not set and no studies found" && exit 1)
	$(PY) scripts/generate_report.py --study-dir $(STUDY_DIR)

clean:
	rm -f $(MANUSCRIPTS_DIR)/*.aux $(MANUSCRIPTS_DIR)/*.log $(MANUSCRIPTS_DIR)/*.out $(MANUSCRIPTS_DIR)/*.toc

# --- Live PDF Watching (auto-recompile on changes) ---
# Requires: entr (brew install entr) and optionally tectonic

.PHONY: watch-methods watch-calibration watch-uncertainty watch-fundingcut

define watch_rule
	@if [ "$(HAVE_ENTR)" != "yes" ]; then \
		echo "entr not found. Install with: brew install entr"; exit 1; \
	fi
	@echo "Watching manuscripts/*.tex; re-compiling $1 on changes..."
	@printf "%s\n" "$(MANUSCRIPTS_DIR)/$1" | $(ENTR) -n -r sh -c \
		'$(MAKE) labels STUDY_DIR=$(STUDY_DIR); \
		 if command -v $(TECTONIC) >/dev/null 2>&1; then cd $(MANUSCRIPTS_DIR) && $(TECTONIC) $1; \
		 else $(TEX) -output-directory=$(MANUSCRIPTS_DIR) $(MANUSCRIPTS_DIR)/$1; fi'
endef

watch-methods:
	$(call watch_rule,paper_methods.tex)

watch-calibration:
	$(call watch_rule,paper_calibration.tex)

watch-uncertainty:
	$(call watch_rule,paper_uncertainty.tex)

watch-fundingcut:
	$(call watch_rule,paper_fundingcut.tex)
