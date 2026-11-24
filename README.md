# Visual openness and student productivity in the BUE library: scripts and anonymised data

Supplementary material to the paper "Does Seeing More Help or Hinder? Visual Openness and Students' Productivity in a University Library Study Area" (ICCAUA). Appendix I of the paper lists what each script does.

## Reproducing the results

1. Python 3.12 with pandas, NumPy, SciPy, statsmodels, Matplotlib, Shapely and ezdxf.
2. `python analysis/run_analysis.py` reads `data/` and the isovist results and writes `results/` (report, tables, figures).

## Data

- `data/responses.csv`: every response to the online task (random response codes; no names or student numbers). Pilot rows are listed in `data/exclusions.csv` with the other excluded responses and the screening rule applied.
- `data/thematic_coding.csv`: themes given to the open answers.
- `data/behaviour_mapping_*`: behavioural mapping records, one file set per day.
- `data/route_counts.csv`: walking lines crossing each count line, by apparent gender and direction (method in `data/route_counts_method.md`; map with `python data/route_density_map.py`).
- `isovist/output/`: isovist area and control of the 152 seats, and the check against depthmapX.
- `drafts/figures/seat_codes_first_floor.csv`: seat codes, positions and facing directions.

The library's CAD plan (`isovist/Library_floor_plans.dxf`), which the isovist scripts read, is not included; it can be requested from the BUE library. Names of researchers in the data are replaced by [researcher].
