"""Validation pilot: 20 seats (4 per area, random, seed 2026) for the manual depthmapX run, plus the
depthmapX command-line results for the same seats and the agreement figures quoted in the paper (Section 2.3).
usage: python pilot20.py <seats.csv> <output folder>"""
import sys, os
import numpy as np, pandas as pd

seats_csv, out = sys.argv[1:3]
s = pd.read_csv(seats_csv)
res = pd.read_csv(os.path.join(out, 'isovist_results_shelves_tall.csv'))
val = pd.read_csv(os.path.join(out, 'validation_depthmapx_shelves_tall.csv'))
pick = pd.concat([g.sample(4, random_state=2026) for _, g in s.groupby('zone')])
p = pick[['code', 'zone', 'x_m', 'y_m', 'facing_deg']].merge(res[['code', 'isovist_area_m2', 'area_170_m2', 'control']], on='code')
p['viewangle_deg'] = 170
sheet = p.rename(columns={'isovist_area_m2': 'script_isovist_area_m2', 'area_170_m2': 'script_area_170_m2', 'control': 'script_control'})
sheet['depthmapx_isovist_area_m2'] = ''; sheet['depthmapx_area_170_m2'] = ''
sheet = sheet[['code', 'zone', 'x_m', 'y_m', 'facing_deg', 'viewangle_deg', 'script_isovist_area_m2', 'script_area_170_m2',
               'script_control', 'depthmapx_isovist_area_m2', 'depthmapx_area_170_m2']]
sheet.to_csv(os.path.join(out, 'validation_pilot_20_seats.csv'), index=False)
cli = val[val.code.isin(pick.code)].merge(pick[['code', 'x_m', 'y_m', 'facing_deg']], on='code')
cli.to_csv(os.path.join(out, 'validation_pilot_20_seats_cli_results.csv'), index=False)
a = cli.diff_area_pct.abs()
print('pilot seats:', ', '.join(pick.code))
print(f'area: mean |diff| {a.mean():.2f}%  max {a.max():.2f}%  r = {np.corrcoef(cli.isovist_area_m2, cli.dmx_area_m2)[0, 1]:.4f}')
print(f'control: max |diff| {cli.diff_control.abs().max():.4f}  r = {np.corrcoef(cli.control, cli.dmx_control)[0, 1]:.4f}')
a = val.diff_area_pct.abs()
print(f'all {len(val)} seats: area mean |diff| {a.mean():.2f}%  max {a.max():.2f}%  r = {np.corrcoef(val.isovist_area_m2, val.dmx_area_m2)[0, 1]:.4f};'
      f' control max |diff| {val.diff_control.abs().max():.4f}')
