import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt


def _safe_rate(numer, denom, scale=1.0):
	denom = denom if denom is not None else 0
	return (numer / denom * scale) if denom and denom > 0 else 0.0


def _load_reference(path: str | None) -> pd.DataFrame | None:
	if not path:
		return None
	if not os.path.exists(path):
		print(f"Reference file not found: {path}")
		return None
	try:
		ref = pd.read_csv(path)
		# Normalize common column names
		ref = ref.rename(columns={
			'prevalence_pct': 'ref_prevalence_pct',
			'prevalence_percent': 'ref_prevalence_pct',
			'incidence_per_1000': 'ref_incidence_per_1000',
			'hiv_mortality_per_1000': 'ref_hiv_mortality_per_1000',
			'mortality_per_1000': 'ref_allcause_mortality_per_1000',
			'allcause_mortality_per_1000': 'ref_allcause_mortality_per_1000',
			'population': 'ref_population',
		})
		return ref
	except Exception as e:
		print(f"Failed to load reference CSV: {e}")
		return None


def _style_axes(ax, title, xlabel, ylabel):
	plt.style.use('seaborn-v0_8-whitegrid')
	ax.set_title(title, fontsize=16, weight='bold', pad=14)
	ax.set_xlabel(xlabel, fontsize=12)
	ax.set_ylabel(ylabel, fontsize=12)
	ax.tick_params(axis='both', which='major', labelsize=11)
	ax.spines['top'].set_visible(False)
	ax.spines['right'].set_visible(False)
	ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.6)


def _plot_series(ax, x, y, label, color, fill=False):
	ax.plot(x, y, color=color, linewidth=2.4, label=label)
	if fill:
		ax.fill_between(x, y, color=color, alpha=0.10)


def main():
	parser = argparse.ArgumentParser(
		description="Generate validation plots (prevalence, incidence, mortality, population)."
	)
	parser.add_argument(
		"--results-file",
		required=True,
		help="Path to simulation_results.csv"
	)
	parser.add_argument(
		"--output-dir",
		required=True,
		help="Directory to save validation plots"
	)
	parser.add_argument(
		"--reference-file",
		default=None,
		help="Optional CSV with columns: year, prevalence_pct, incidence_per_1000, (hiv_)mortality_per_1000, population"
	)
	parser.add_argument(
		"--xmin", type=int, default=1990,
		help="X-axis minimum year"
	)
	parser.add_argument(
		"--xmax", type=int, default=2022,
		help="X-axis maximum year"
	)
	args = parser.parse_args()

	os.makedirs(args.output_dir, exist_ok=True)
	df = pd.read_csv(args.results_file)

	# Derived metrics
	df['prevalence_pct'] = df['hiv_prevalence'] * 100.0
	df['incidence_per_1000'] = [
		_safe_rate(n, s, 1000.0) for n, s in zip(df['new_infections'], df['susceptible'])
	]
	df['hiv_mortality_per_1000'] = [
		_safe_rate(d, p, 1000.0) for d, p in zip(df['deaths_hiv'], df['total_population'])
	]
	df['allcause_mortality_per_1000'] = [
		_safe_rate(dh + dn, p, 1000.0)
		for dh, dn, p in zip(df['deaths_hiv'], df['deaths_natural'], df['total_population'])
	]

	ref = _load_reference(args.reference_file)
	if ref is not None:
		df = df.merge(ref, how='left', on='year')

	# Common x
	x = df['year']

	# Colors
	c_sim = {
		'prev': '#d62728',
		'inc': '#1f77b4',
		'mort_hiv': '#2ca02c',
		'mort_all': '#8c564b',
		'pop': '#9467bd',
	}
	c_ref = '#111111'

	# 1) Prevalence
	fig, ax = plt.subplots(figsize=(10, 6))
	_style_axes(ax, 'HIV Prevalence, Cameroon (1990–2022)', 'Year', 'Prevalence (%)')
	_plot_series(ax, x, df['prevalence_pct'], 'Model', c_sim['prev'], fill=True)
	if ref is not None and 'ref_prevalence_pct' in df.columns:
		_plot_series(ax, x, df['ref_prevalence_pct'], 'Reference', c_ref)
	ax.set_xlim(args.xmin, args.xmax)
	ax.legend(frameon=False, fontsize=11)
	out = os.path.join(args.output_dir, f"validation_prevalence_{pd.Timestamp.now():%Y%m%d_%H%M%S}.png")
	plt.tight_layout(); plt.savefig(out, dpi=300, bbox_inches='tight'); plt.close(fig)
	print(f"Saved: {out}")

	# 2) Incidence per 1,000 susceptible
	fig, ax = plt.subplots(figsize=(10, 6))
	_style_axes(ax, 'HIV Incidence Rate (per 1,000 susceptible), 1990–2022', 'Year', 'Incidence per 1,000')
	_plot_series(ax, x, df['incidence_per_1000'], 'Model', c_sim['inc'], fill=True)
	if ref is not None and 'ref_incidence_per_1000' in df.columns:
		_plot_series(ax, x, df['ref_incidence_per_1000'], 'Reference', c_ref)
	ax.set_xlim(args.xmin, args.xmax)
	ax.legend(frameon=False, fontsize=11)
	out = os.path.join(args.output_dir, f"validation_incidence_{pd.Timestamp.now():%Y%m%d_%H%M%S}.png")
	plt.tight_layout(); plt.savefig(out, dpi=300, bbox_inches='tight'); plt.close(fig)
	print(f"Saved: {out}")

	# 3) HIV-specific mortality per 1,000
	fig, ax = plt.subplots(figsize=(10, 6))
	_style_axes(ax, 'HIV-related Mortality (per 1,000 population), 1990–2022', 'Year', 'HIV mortality per 1,000')
	_plot_series(ax, x, df['hiv_mortality_per_1000'], 'Model', c_sim['mort_hiv'], fill=True)
	if ref is not None and 'ref_hiv_mortality_per_1000' in df.columns:
		_plot_series(ax, x, df['ref_hiv_mortality_per_1000'], 'Reference', c_ref)
	ax.set_xlim(args.xmin, args.xmax)
	ax.legend(frameon=False, fontsize=11)
	out = os.path.join(args.output_dir, f"validation_mortality_hiv_{pd.Timestamp.now():%Y%m%d_%H%M%S}.png")
	plt.tight_layout(); plt.savefig(out, dpi=300, bbox_inches='tight'); plt.close(fig)
	print(f"Saved: {out}")

	# 4) All-cause mortality per 1,000
	fig, ax = plt.subplots(figsize=(10, 6))
	_style_axes(ax, 'All-cause Mortality (per 1,000 population), 1990–2022', 'Year', 'All-cause mortality per 1,000')
	_plot_series(ax, x, df['allcause_mortality_per_1000'], 'Model', c_sim['mort_all'], fill=True)
	if ref is not None and 'ref_allcause_mortality_per_1000' in df.columns:
		_plot_series(ax, x, df['ref_allcause_mortality_per_1000'], 'Reference', c_ref)
	ax.set_xlim(args.xmin, args.xmax)
	ax.legend(frameon=False, fontsize=11)
	out = os.path.join(args.output_dir, f"validation_mortality_allcause_{pd.Timestamp.now():%Y%m%d_%H%M%S}.png")
	plt.tight_layout(); plt.savefig(out, dpi=300, bbox_inches='tight'); plt.close(fig)
	print(f"Saved: {out}")

	# 5) Population growth
	fig, ax = plt.subplots(figsize=(10, 6))
	_style_axes(ax, 'Total Population (Model), 1990–2022', 'Year', 'Population (count)')
	_plot_series(ax, x, df['total_population'], 'Model', c_sim['pop'])
	if ref is not None and 'ref_population' in df.columns:
		_plot_series(ax, x, df['ref_population'], 'Reference', c_ref)
	ax.set_xlim(args.xmin, args.xmax)
	ax.legend(frameon=False, fontsize=11)
	out = os.path.join(args.output_dir, f"validation_population_{pd.Timestamp.now():%Y%m%d_%H%M%S}.png")
	plt.tight_layout(); plt.savefig(out, dpi=300, bbox_inches='tight'); plt.close(fig)
	print(f"Saved: {out}")


if __name__ == "__main__":
	main()

