"""BUE library study - complete analysis in one run.

    python run_analysis.py            (from writing/analysis, or give the path)

Reads only plain files in writing/data and writing/isovist/output, and writes everything to writing/results:
  report.md            all numbers, in the order of Section 2.7 of the paper
  results.xlsx         the same tables, one sheet each
  tables/*.csv         every table as CSV
  figures/*.png        scatter plots, openness map, behaviour maps
  participants.csv     one row per valid participant (scores + seat openness)
  thematic_export.csv  open answers of valid participants, with seat openness, ready for coding
There is no randomness anywhere: the same input files always give the same numbers.

Inputs (see README.md in this folder for how to update them):
  data/responses.csv                    Google Sheet export (File > Download > CSV), 'Seat code' on the 152-seat plan
  data/exclusions.csv                   code, category, reason - pilot rows and excluded responses (human decision)
  data/behaviour_mapping_<date>.csv     long format: one row per seat per scan (written by the transcription script), or
  data/mapping_<date>_wide.csv          wide template: seat, zone, scan_1, scan_2 ... (+ mapping_<date>_scans.csv)
  data/*_extras.csv                     extra chairs per table (optional)
  data/thematic_coding.csv              codes for the open answers (reviewed); falls back to thematic_coding_DRAFT.csv
  ../drafts/figures/seat_codes_first_floor.csv, ../isovist/output/isovist_results_shelves_tall.csv
"""
import os, sys, glob, json, re, datetime, subprocess
import numpy as np, pandas as pd
from scipy import stats, integrate
import statsmodels.formula.api as smf
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(HERE)
DATA, RES = os.path.join(W, 'data'), os.path.join(W, 'results')
FIG, TAB = os.path.join(RES, 'figures'), os.path.join(RES, 'tables')
for p in (RES, FIG, TAB): os.makedirs(p, exist_ok=True)

KEY = list('CADBDACBDABCDBACDACB')              # task v2 (14 Nov 2026)
LIMIT_S = 900                                   # 15-minute limit
GPA = {'Below 2.00': 1, '2.00 – 2.49': 2, '2.50 – 2.99': 3, '3.00 – 3.49': 4, '3.50 – 4.00': 5}
REASON = {'The table was empty, so I sat here.': 'table empty', 'This is where I usually sit.': 'usual seat',
          'It is close to something I need (for example, a power socket or a window).': 'near something needed',
          'I wanted to sit near my friends.': 'near friends',
          'I like what I can see from here, or how open or closed-in it feels.': 'likes the view / openness', 'Other': 'other'}
OUTCOMES = {'bis': 'Productivity index (BIS)', 'quantity': 'Quantity (questions attempted)',
            'quality': 'Quality (proportion correct)', 'time_min': 'Time (minutes)'}
OPENNESS = {'isovist_area_m2': 'Isovist area (m²)', 'control': 'Control (A170/A360)'}
INK, INK2, GRID, SURF, BLUE = '#0b0b0b', '#52514e', '#d9d8d3', '#fcfcfb', '#2a78d6'
plt.rcParams.update({'font.family': 'Arial', 'font.size': 9})
REPORT, TABLES = [], {}


def say(s=''): REPORT.append(s)


def table(name, df, title=None, floatfmt=3):
    TABLES[name] = df
    df.to_csv(os.path.join(TAB, name + '.csv'), index=False)
    if title: say(f'**{title}**'); say()
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]): d[c] = d[c].map(lambda v: '' if pd.isna(v) else f'{v:.{floatfmt}f}')
    say('| ' + ' | '.join(map(str, d.columns)) + ' |'); say('|' + '---|' * len(d.columns))
    for r in d.itertuples(index=False): say('| ' + ' | '.join('' if pd.isna(v) else str(v) for v in r) + ' |')
    say()


# ---------- statistics helpers ----------
def bf10_corr(r, n):
    """Jeffreys' approximate Bayes factor for a correlation, uniform prior on rho (Wetzels & Wagenmakers, 2012);
    applied to Spearman's rho via the ranks. BF10 > 1 favours an association, BF01 = 1/BF10 favours none."""
    if n < 4 or not np.isfinite(r): return np.nan
    f = lambda p: np.exp((n - 1) / 2 * np.log1p(-p * p) - (n - 1.5) * np.log1p(-p * r))
    v, _ = integrate.quad(f, -1, 1, limit=200)
    return v / 2


def spearman(x, y):
    m = x.notna() & y.notna(); n = int(m.sum())
    if n < 4: return n, np.nan, np.nan, np.nan
    rho, p = stats.spearmanr(x[m], y[m])
    return n, rho, p, bf10_corr(rho, n)


def bf_words(bf10):
    if not np.isfinite(bf10): return ''
    b, side = (bf10, 'association') if bf10 >= 1 else (1 / bf10, 'no association')
    lvl = 'anecdotal' if b < 3 else 'moderate' if b < 10 else 'strong' if b < 30 else 'very strong'
    return f'{lvl} evidence for {side}'


# ---------- 1. responses ----------
def load_responses():
    r = pd.read_csv(os.path.join(DATA, 'responses.csv'), dtype=str, keep_default_na=False)
    r['code'] = r['Response code'].str.split().str[0].str.strip()
    ex = pd.read_csv(os.path.join(DATA, 'exclusions.csv'), dtype=str, keep_default_na=False)
    r = r.merge(ex[['code', 'category', 'reason']].rename(columns={'reason': 'exclusion_reason'}), on='code', how='left')
    r['category'] = r['category'].replace('', np.nan).fillna('valid')
    qcols = [c for c in r.columns if re.match(r'^Q\d+ \(', c)]
    assert len(qcols) == 20, 'expected 20 answer columns'
    ans = r[qcols].apply(lambda s: s.str.strip().where(s.str.strip().isin(list('ABCD')), ''))
    r['quantity'] = (ans != '').sum(axis=1)
    r['correct'] = sum((ans[c] == KEY[i]).astype(int) for i, c in enumerate(qcols))
    r['quality'] = np.where(r.quantity > 0, r.correct / r.quantity.replace(0, np.nan), np.nan)
    r['time_s'] = pd.to_numeric(r['Task time (s)'], errors='coerce').clip(upper=LIMIT_S)
    r['time_min'] = r.time_s / 60
    r['timed_out'] = r['Ended by'].str.strip().eq('time limit')
    r['seat'] = r['Seat code'].str.strip(); r['area_letter'] = r['Area'].str.strip()
    r['gpa_band'] = r['GPA band'].str.strip(); r['gpa'] = r.gpa_band.map(GPA)
    r['reason'] = r['Seat reason'].str.strip().map(REASON).fillna(r['Seat reason'].str.strip())
    return r, ex


def main():
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    say('# BUE library study - analysis report'); say()
    say(f'Generated {stamp} by `analysis/run_analysis.py` from the files in `data/`. Re-running it on the same files gives the same numbers.'); say()

    seats = pd.read_csv(os.path.join(W, 'drafts', 'figures', 'seat_codes_first_floor.csv'))
    iso = pd.read_csv(os.path.join(W, 'isovist', 'output', 'isovist_results_shelves_tall.csv'))[['code', 'isovist_area_m2', 'area_170_m2', 'control']]
    r, ex = load_responses()

    # sample flow
    say('## 1. Sample'); say()
    flow = r.groupby('category').size().reindex(['valid', 'pilot', 'ai', 'not_engaged']).fillna(0).astype(int)
    unknown_ex = sorted(set(ex.code) - set(r.code))
    table('sample_flow', pd.DataFrame({'group': ['responses in the sheet', 'pilot rows', 'excluded: AI use (fast + accurate, or admitted)',
                                                 'excluded: no real attempt', 'valid'],
                                       'n': [len(r), flow['pilot'], flow['ai'], flow['not_engaged'], flow['valid']]}), 'Sample')
    if unknown_ex: say(f'Note: codes in exclusions.csv not found in responses.csv: {", ".join(unknown_ex)}'); say()
    table('exclusions', r[r.category != 'valid'][['code', 'seat', 'category', 'time_s', 'quantity', 'correct', 'exclusion_reason']]
          .rename(columns={'time_s': 'time (s)', 'exclusion_reason': 'reason'}), 'Excluded responses', 1)

    v = r[r.category == 'valid'].merge(iso, left_on='seat', right_on='code', how='left', suffixes=('', '_iso'))
    missing = v[v.isovist_area_m2.isna()].seat.tolist()
    assert not missing, f'seat codes not on the 152-seat plan: {missing}'
    zq, zt = (v.quality - v.quality.mean()) / v.quality.std(), (v.time_s - v.time_s.mean()) / v.time_s.std()
    v['bis'] = zq - zt                       # balanced integration score (Liesefeld & Janczyk, 2019)
    med = v.isovist_area_m2.median()
    v['openness_group'] = np.where(v.isovist_area_m2 >= med, 'more open', 'more enclosed')
    keep = ['code', 'seat', 'area_letter', 'isovist_area_m2', 'control', 'openness_group', 'quantity', 'correct', 'quality',
            'time_s', 'time_min', 'timed_out', 'bis', 'gpa_band', 'gpa', 'reason', 'Seat reason (other)', 'Open Q1', 'Open Q2']
    v[keep].to_csv(os.path.join(RES, 'participants.csv'), index=False)
    n = len(v)
    say(f'Valid participants: **{n}** at {v.seat.nunique()} different seats in {v.area_letter.nunique()} areas; '
        f'{int(v.timed_out.sum())} reached the 15-minute limit. Median isovist area of their seats: {med:.0f} m².'); say()

    # ---------- 2. description ----------
    say('## 2. Description (Section 2.7, step 1)'); say()
    rows = []
    for col, lab in list(OPENNESS.items()) + list(OUTCOMES.items()):
        s = v[col].astype(float)
        rows.append(dict(variable=lab, n=int(s.notna().sum()), mean=s.mean(), sd=s.std(), median=s.median(), min=s.min(), max=s.max()))
    table('descriptives', pd.DataFrame(rows), 'Valid participants: openness of their seat and task results', 2)
    by = v.groupby('area_letter').agg(n=('code', 'size'), isovist_area=('isovist_area_m2', 'mean'), control=('control', 'mean'),
                                      quantity=('quantity', 'mean'), quality=('quality', 'mean'), time_min=('time_min', 'mean'),
                                      bis=('bis', 'mean')).reset_index().rename(columns={'area_letter': 'area'})
    table('by_area', by, 'Means by area', 2)
    allseats = iso.merge(seats[['code', 'zone']], on='code')
    agg = dict(seats=('code', 'size'), area_min=('isovist_area_m2', 'min'), area_mean=('isovist_area_m2', 'mean'),
               area_max=('isovist_area_m2', 'max'), control_min=('control', 'min'), control_mean=('control', 'mean'),
               control_max=('control', 'max'))
    so = pd.concat([allseats.groupby('zone').agg(**agg).reset_index(),
                    allseats.assign(zone='all').groupby('zone').agg(**agg).reset_index()], ignore_index=True)
    table('seat_openness_all', so, 'Openness of all 152 seats, by area', 2)
    g = v.groupby('gpa_band', dropna=False).size().reset_index(name='n')
    table('gpa_bands', g, 'GPA band (closed question)')
    table('seat_reasons', v.groupby('reason').size().reset_index(name='n').sort_values('n', ascending=False), 'Main reason for choosing the seat')

    # ---------- 3. main test ----------
    say('## 3. Main test: Spearman correlations (step 2, first part; step 4 components; step 5 Bayes factors)'); say()
    rows = []
    for oc, olab in OPENNESS.items():
        for yc, ylab in OUTCOMES.items():
            nn, rho, p, bf = spearman(v[oc], v[yc])
            # 95% interval for Spearman's rho: Fisher z with the Bonett & Wright (2000) standard error sqrt((1 + rho^2/2) / (n - 3))
            se = np.sqrt((1 + rho ** 2 / 2) / (nn - 3)); zr = np.arctanh(rho)
            lo, hi = np.tanh(zr - 1.959964 * se), np.tanh(zr + 1.959964 * se)
            rows.append(dict(openness=olab, outcome=ylab, n=nn, rho=rho, ci_low=lo, ci_high=hi, p=p, BF10=bf, BF01=1 / bf if bf else np.nan,
                             reading=bf_words(bf)))
    corr = pd.DataFrame(rows)
    table('correlations', corr, 'Spearman correlations between seat openness and productivity')
    say('BF10 = how many times more likely the data are if there is an association than if there is none (BF01 = the reverse). '
        'Bayes factors are reported for every test; Section 2.7 uses them to interpret non-significant results. '
        'Labels follow the usual 1-3 / 3-10 / 10-30 / >30 bands.'); say()

    # ---------- 4. regression ----------
    say('## 4. Regression (step 2, second part; step 3 inverted U)'); say()
    d = v.copy()
    for c in ('isovist_area_m2', 'control'):
        d['z_' + c] = (d[c] - d[c].mean()) / d[c].std()
    d['z_area_sq'] = d.z_isovist_area_m2 ** 2
    d['reason_c'] = d.reason.where(d.reason.map(d.reason.value_counts()) >= 3, 'other / rare')
    # 18 Nov 2026 (user decision): fewer than half gave a usable GPA, so GPA is not a control in the main models;
    # the GPA model is kept only as a side check (M3) on the students who gave one.
    models = [('M1 openness', 'bis ~ z_isovist_area_m2 + z_control', d),
              ('M2 + seat reason', 'bis ~ z_isovist_area_m2 + z_control + C(reason_c)', d),
              ('M3 + seat reason + GPA band (side check, students with a GPA)', 'bis ~ z_isovist_area_m2 + z_control + C(reason_c) + gpa',
               d.dropna(subset=['gpa'])),
              ('M4 inverted U (area squared)', 'bis ~ z_isovist_area_m2 + z_area_sq + z_control', d)]
    rows, fits = [], []
    for name, f, dd in models:
        k = len(re.findall(r'\+', f)) + 1
        if len(dd) < k + 5:
            fits.append(dict(model=name, n=len(dd), note=f'not estimated: only {len(dd)} cases for {k} predictors')); continue
        m = smf.ols(f, data=dd).fit()
        fits.append(dict(model=name, n=int(m.nobs), R2=m.rsquared, adj_R2=m.rsquared_adj, F_p=m.f_pvalue, note=''))
        for term in m.params.index:
            if term == 'Intercept': continue
            rows.append(dict(model=name, term=term, b=m.params[term], SE=m.bse[term], p=m.pvalues[term]))
    table('regression_fit', pd.DataFrame(fits), 'Regression of the productivity index: model fit')
    table('regression_terms', pd.DataFrame(rows), 'Regression coefficients (openness measures standardised: b = change in BIS per 1 SD)')
    n_gpa = int(d.gpa.notna().sum())
    say(f'Usable GPA band: {n_gpa} of {len(d)} valid participants (the rest have no GPA yet or preferred not to say). '
        'GPA is therefore not a control in the main models; M3 is a side check on those who gave one '
        '(ordinal score 1 = below 2.00 ... 5 = 3.50-4.00). Seat reasons with fewer than 3 students are pooled. '
        'With the current sample these models are exploratory.'); say()
    rows = []
    for yc, ylab in list(OUTCOMES.items())[1:]:
        m = smf.ols(f'{yc} ~ z_isovist_area_m2 + z_control', data=d.dropna(subset=[yc])).fit()
        for term in ('z_isovist_area_m2', 'z_control'):
            rows.append(dict(outcome=ylab, term=term, b=m.params[term], SE=m.bse[term], p=m.pvalues[term], n=int(m.nobs), R2=m.rsquared))
    table('regression_components', pd.DataFrame(rows), 'Components one by one (step 4): each regressed on isovist area and control')

    # ---------- 5. behaviour mapping ----------
    say('## 5. Behavioural mapping'); say()
    mp = load_mapping(seats)
    if mp is None or mp.empty:
        say('No mapping files found.'); say()
    else:
        scans = mp.groupby(['date', 'scan']).agg(start=('start', 'min'), end=('end', 'max'),
                                                  studying=('mark', lambda s: (s == 'S').sum()), talking=('mark', lambda s: (s == 'T').sum()),
                                                  phone=('mark', lambda s: (s == 'P').sum()), other=('mark', lambda s: (s == 'O').sum()),
                                                  unreadable=('mark', lambda s: (s == 'U').sum()), belongings=('mark', lambda s: (s == 'B').sum()), missing=('mark', lambda s: (s == 'X').sum())).reset_index()
        ext = load_extras()
        if ext is not None:
            pe = ext[ext.activity.astype(str).str.strip().isin(list('STPOLU'))].groupby(['date', 'scan'])['count'].sum().rename('people_on_extra_chairs')
            scans = scans.merge(pe.reset_index(), on=['date', 'scan'], how='left').fillna({'people_on_extra_chairs': 0})
        table('mapping_scans', scans, 'Each scan: standard seats by activity (plus people on extra chairs)')
        ps = mp.groupby('seat').agg(scans=('scan', 'size'), occupied=('occupied', 'sum'),
                                    studying=('mark', lambda s: (s == 'S').sum()), known=('mark', lambda s: s.isin(list('STPOL')).sum()),
                                    present=('mark', lambda s: (s != 'X').sum())).reset_index()
        ps['occupancy_rate'] = ps.occupied / ps.present.replace(0, np.nan)
        ps['study_share'] = ps.studying / ps.known.replace(0, np.nan)          # U (letter unreadable) left out of the share
        ps = ps.merge(iso, left_on='seat', right_on='code').merge(seats[['code', 'zone']], on='code')
        ps.to_csv(os.path.join(RES, 'mapping_per_seat.csv'), index=False)
        rows = []
        for oc, olab in OPENNESS.items():
            for yc, ylab, sub in (('occupancy_rate', 'Occupancy rate (share of scans occupied, chair present)', ps),
                                  ('study_share', 'Study share (scans studying / scans occupied, activity readable)', ps[ps.known > 0])):
                nn, rho, p, bf = spearman(sub[oc], sub[yc])
                rows.append(dict(openness=olab, measure=ylab, seats=nn, rho=rho, p=p, BF10=bf, reading=bf_words(bf)))
        table('mapping_correlations', pd.DataFrame(rows), 'Seat openness vs observed use (all seats with the chair present; study share only for seats ever occupied)')
        whole_floor(mp, ext)
        say(f'Mapping days: {", ".join(sorted(mp.date.unique()))}; {mp.groupby(["date", "scan"]).ngroups} scans. '
            'Observed study behaviour is exploratory until it is confirmed as a second outcome.'); say()
        # all scans of all days together: one map for the paper (each day's map goes in the appendix)
        subprocess.run([sys.executable, os.path.join(DATA, 'behaviour_map_merged.py'), os.path.join(FIG, 'behaviour_map_all_scans.png')],
                       check=True, capture_output=True)
        say(f'Merged behaviour map (all scans): `results/figures/behaviour_map_all_scans.png`'); say()
        for dt in sorted(mp.date.unique()):
            src = os.path.join(DATA, f'behaviour_mapping_{dt}.csv')
            if os.path.exists(src):
                out = os.path.join(FIG, f'behaviour_map_{dt}.png')
                subprocess.run([sys.executable, os.path.join(DATA, 'behaviour_map.py'), dt, out], check=True, capture_output=True)
                say(f'Behaviour map: `results/figures/behaviour_map_{dt}.png`'); say()

    # ---------- 6. thematic analysis ----------
    say('## 6. Open answers (thematic analysis)'); say()
    th = v[['code', 'seat', 'area_letter', 'isovist_area_m2', 'control', 'openness_group', 'Open Q1', 'Open Q2']]
    th.to_csv(os.path.join(RES, 'thematic_export.csv'), index=False)
    cf = os.path.join(DATA, 'thematic_coding.csv'); draft = not os.path.exists(cf)
    if draft: cf = os.path.join(DATA, 'thematic_coding_DRAFT.csv')
    if os.path.exists(cf):
        c = pd.read_csv(cf, dtype=str, keep_default_na=False)
        c = c[c.code.isin(v.code)]
        long = c.assign(theme=c.themes.str.split(';')).explode('theme')
        long['theme'] = long.theme.str.strip(); long = long[long.theme != '']
        long = long.merge(v[['code', 'openness_group']], on='code')
        t = long.groupby('theme').agg(n=('code', 'nunique')).reset_index()
        for gname in ('more open', 'more enclosed'):
            t[gname] = t.theme.map(long[long.openness_group == gname].groupby('theme').code.nunique()).fillna(0).astype(int)
        t['% of participants'] = (100 * t.n / len(v)).round(0)
        t = t.sort_values('n', ascending=False)
        n_open = int((v.openness_group == 'more open').sum())
        table('themes', t, f'Themes in the open answers{" (DRAFT coding - to be checked by the researchers)" if draft else ""} '
                           f'- participants mentioning each theme; more open seats n = {n_open}, more enclosed n = {len(v) - n_open}')
        missing_c = sorted(set(v.code) - set(c.code))
        if missing_c: say(f'Not yet coded: {", ".join(missing_c)}'); say()
    else:
        say('No coding file yet: code the answers in `results/thematic_export.csv` and save them as `data/thematic_coding.csv`.'); say()

    # ---------- figures ----------
    scatter_grid(v)
    main_figure(v)
    openness_map(seats, iso, v)
    say('## 7. Figures'); say()
    for f in sorted(os.listdir(FIG)): say(f'- `results/figures/{f}`')
    say()

    # ---------- write ----------
    with open(os.path.join(RES, 'report.md'), 'w', encoding='utf-8') as fh: fh.write('\n'.join(REPORT))
    with pd.ExcelWriter(os.path.join(RES, 'results.xlsx')) as xw:
        for k, df in TABLES.items(): df.to_excel(xw, sheet_name=k[:31], index=False)
    key = dict(generated=stamp, n_valid=n, n_responses=len(r),
               main=corr[corr.outcome == OUTCOMES['bis']][['openness', 'rho', 'p', 'BF10']].to_dict('records'))
    with open(os.path.join(RES, 'key_numbers.json'), 'w', encoding='utf-8') as fh: json.dump(key, fh, indent=1, default=float)
    print(f'done: {n} valid participants; report at {os.path.join(RES, "report.md")}')


# ---------- whole-floor mapping (sheets v3, from 19 Nov 2026) ----------
ACT = {'S': 'studying', 'T': 'talking', 'P': 'phone', 'O': 'other', 'L': 'looking for books'}


def whole_floor(mp, ext):
    """Days mapped with the whole-floor sheets have a *_people_off_seats.csv file (standing, walking, sitting away from a table).
    Reports, per scan: where people were (standard seats / extra chairs / off the seats), what they were doing, gender and area."""
    fs = sorted(glob.glob(os.path.join(DATA, 'behaviour_mapping_*_people_off_seats.csv')))
    if not fs: return
    off = pd.concat([pd.read_csv(f, keep_default_na=False).assign(date=re.search(r'(\d{4}-\d{2}-\d{2})', f).group(1)) for f in fs])
    off['count'] = pd.to_numeric(off['count'])
    days = sorted(off.date.unique())
    say('### Whole floor (days mapped with the whole-floor sheets)'); say()
    seat = mp[mp.date.isin(days) & (mp.occupied == 1)].copy(); seat['count'] = 1; seat['where'] = 'standard seat'
    seat['area'] = seat.zone; seat['activity'] = seat.mark
    if 'gender' not in seat: seat['gender'] = ''
    ex_ = ext[ext.date.isin(days)].copy() if ext is not None else pd.DataFrame(columns=['date', 'scan', 'count', 'activity'])
    ex_ = ex_[ex_.activity.astype(str).str.strip().isin(list('STPOLU'))].copy()
    ex_['where'] = 'extra chair'; ex_['area'] = ex_.table_first_seat.str[0]
    if 'gender' not in ex_: ex_['gender'] = ''
    off_ = off[off.staff.astype(str).str.strip() != '1'].copy()   # staff left out of all people counts (researchers, 24 Nov 2026)
    off_['where'] = off_.posture.map({'stand': 'standing', 'walk': 'walking', 'sit_other': 'sitting away from a table',
                                      'sit_else': 'sitting on the floor / ledge'})
    cols = ['date', 'scan', 'area', 'where', 'activity', 'gender', 'count']
    allp = pd.concat([seat[cols], ex_[cols], off_[cols]], ignore_index=True)
    allp['activity'] = allp.activity.astype(str).str.strip().replace('', 'not recorded')
    allp['gender'] = allp.gender.astype(str).str.strip().replace({'': 'not recorded', 'U': 'cannot tell', 'M': 'male', 'F': 'female'})
    allp['scan'] = allp.scan.astype(int)
    allp.to_csv(os.path.join(RES, 'mapping_whole_floor_people.csv'), index=False)
    piv = lambda col: allp.pivot_table(index=['date', 'scan'], columns=col, values='count', aggfunc='sum', fill_value=0).reset_index()
    w = piv('where'); w['total'] = w.drop(columns=['date', 'scan']).sum(axis=1)
    table('floor_where', w, 'People on the floor per scan, by where they were')
    a = piv('activity').rename(columns=ACT); table('floor_activity', a, 'People on the floor per scan, by activity (standing/walking: activity only when written)')
    g = piv('gender'); table('floor_gender', g, 'People on the floor per scan, by gender (pen colour)')
    ar = piv('area'); table('floor_area', ar, 'People on the floor per scan, by area')
    st = allp[allp['where'].isin(['standard seat', 'extra chair'])]
    sa = st.groupby('area').apply(lambda d: pd.Series({'people seated': d['count'].sum(),
                                                       'studying': d.loc[d.activity == 'S', 'count'].sum()}), include_groups=False).reset_index()
    sa['study share'] = sa.studying / sa['people seated']
    table('floor_area_study', sa, 'Seated people by area, all whole-floor scans together: share studying', 2)
    say('Walking routes and observers\' notes: see data/behaviour_mapping_<date>_notes.txt (qualitative).'); say()


# ---------- mapping input ----------
def load_mapping(seats):
    parts = []
    for f in sorted(glob.glob(os.path.join(DATA, 'behaviour_mapping_*.csv'))):
        if f.endswith('_extras.csv') or f.endswith('_people_off_seats.csv'): continue
        parts.append(pd.read_csv(f, dtype={'mark': str}, keep_default_na=False))
    for f in sorted(glob.glob(os.path.join(DATA, 'mapping_*_wide.csv'))):          # hand-typed template
        dt = re.search(r'mapping_(.+)_wide\.csv', os.path.basename(f)).group(1)
        w = pd.read_csv(f, dtype=str, keep_default_na=False)
        meta_f = f.replace('_wide.csv', '_scans.csv')
        meta = pd.read_csv(meta_f, dtype=str, keep_default_na=False).set_index('scan') if os.path.exists(meta_f) else None
        for col in [c for c in w.columns if c.startswith('scan_')]:
            sc = int(col.split('_')[1])
            if not w[col].str.strip().any(): continue
            m = w[['seat', 'zone']].copy(); m['mark'] = w[col].str.strip().str.upper()
            m['date'], m['scan'] = dt, sc
            m['start'] = meta.loc[str(sc), 'start'] if meta is not None and str(sc) in meta.index else ''
            m['end'] = meta.loc[str(sc), 'end'] if meta is not None and str(sc) in meta.index else ''
            m['occupied'] = m.mark.isin(list('STPOLU')).astype(int)
            parts.append(m)
    if not parts: return None
    mp = pd.concat(parts, ignore_index=True)
    mp['mark'] = mp['mark'].fillna('').astype(str).str.strip().str.upper()
    mp['date'] = mp['date'].astype(str)
    mp['occupied'] = mp.mark.isin(list('STPOLU')).astype(int)   # U = person there, letter unreadable
    bad = sorted(set(mp.seat) - set(seats.code))
    assert not bad, f'mapping seats not on the plan: {bad}'
    return mp


def load_extras():
    fs = glob.glob(os.path.join(DATA, '*_extras.csv'))
    if not fs: return None
    out = []
    for f in fs:
        e = pd.read_csv(f, keep_default_na=False)
        if 'date' not in e.columns: e['date'] = re.search(r'(\d{4}-\d{2}-\d{2})', f).group(1)
        e['count'] = pd.to_numeric(e['count'], errors='coerce').fillna(0)
        out.append(e)
    return pd.concat(out, ignore_index=True)


# ---------- figures ----------
def scatter_grid(v):
    fig, axs = plt.subplots(2, 4, figsize=(12, 6), facecolor=SURF)
    for i, (oc, olab) in enumerate(OPENNESS.items()):
        for j, (yc, ylab) in enumerate(OUTCOMES.items()):
            ax = axs[i, j]; ax.set_facecolor(SURF)
            ax.scatter(v[oc], v[yc], s=36, color=BLUE, edgecolor=SURF, linewidth=1.2, zorder=3)
            nn, rho, p, bf = spearman(v[oc], v[yc])
            ax.set_title(f'ρ = {rho:.2f}, p = {p:.2f}, n = {nn}', fontsize=8.5, color=INK2, loc='left')
            ax.set_xlabel(olab, fontsize=8.5, color=INK2); ax.set_ylabel(ylab, fontsize=8.5, color=INK2)
            ax.grid(color=GRID, lw=0.5); ax.set_axisbelow(True)
            for s in ('top', 'right'): ax.spines[s].set_visible(False)
            for s in ('left', 'bottom'): ax.spines[s].set_color(GRID)
            ax.tick_params(colors=INK2, labelsize=8)
    fig.suptitle('Seat openness and task results (valid participants; Spearman ρ)', x=0.01, ha='left', fontsize=11, color=INK)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'scatter_openness_vs_productivity.png'), dpi=200, facecolor=SURF); plt.close(fig)


def main_figure(v):
    """Paper Figure 6 (simple version, added 18 Nov 2026): isovist area against the index and each component, one panel each,
    with the result written in plain words in the panel title. The full 8-panel grid (incl. control) goes to the appendices."""
    ylab = {'bis': 'Productivity index (0 = average)', 'quantity': 'Questions attempted (of 20)',
            'quality': 'Share answered correctly', 'time_min': 'Minutes on the task (limit 15)'}
    name = {'bis': 'Productivity index', 'quantity': 'Quantity', 'quality': 'Quality', 'time_min': 'Time'}
    more = {'bis': ('higher index', 'lower index'), 'quantity': ('more questions', 'fewer questions'),
            'quality': ('more accurate', 'less accurate'), 'time_min': ('more time', 'less time')}
    # 18 Nov 2026: reduced to the two charts that answer the questions (index = main question, time = the one link);
    # quantity and quality stay in Table 7 and in the full grid (appendix Figure F1)
    # 24 Nov 2026 (user): with the final data the time link is gone, so the second chart shows quantity, the strongest trend
    fig, axs = plt.subplots(1, 2, figsize=(8.4, 3.6), facecolor=SURF)
    for ax, yc in zip(axs, ['bis', 'quantity']):
        ax.set_facecolor(SURF)
        x, y = v.isovist_area_m2.astype(float), v[yc].astype(float)
        nn, rho, p, bf = spearman(x, y)
        # no straight trend line: Spearman is rank-based, and a line would run past the 15-minute limit
        ax.scatter(x, y, s=36, color=BLUE, edgecolor=SURF, linewidth=1.2, zorder=3)
        verdict = f'more open seat → {more[yc][0] if rho > 0 else more[yc][1]}' if p < .05 else 'no clear link'
        ax.set_title(f'{name[yc]}: {verdict}\nρ = {rho:.2f}, p = {p:.2f}'.replace('-', '−'), fontsize=9, color=INK, loc='left')
        ax.set_xlabel('Isovist area of the seat (m²)', fontsize=8.5, color=INK2); ax.set_ylabel(ylab[yc], fontsize=8.5, color=INK2)
        if yc == 'time_min': ax.set_ylim(6, 15.5)          # supervisor (18 Nov 2026): time axis starts at 6 minutes
        if yc == 'quantity': ax.set_ylim(0, 20.8)
        ax.grid(color=GRID, lw=0.5); ax.set_axisbelow(True)
        for s in ('top', 'right'): ax.spines[s].set_visible(False)
        for s in ('left', 'bottom'): ax.spines[s].set_color(GRID)
        ax.tick_params(colors=INK2, labelsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'openness_vs_productivity_main.png'), dpi=220, facecolor=SURF); plt.close(fig)


def openness_map(seats, iso, v):
    """Paper Figure 5: every seat shaded by isovist area (one-hue sequential scale), with the isovists of the most open
    and the most enclosed seat outlined; seats of valid participants ringed."""
    sys.path.insert(0, os.path.join(W, 'isovist'))
    import standard_layout as L
    from matplotlib.patches import Polygon as MplPoly, Rectangle
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    WIN = (786.0, 836.6, -1340.0, -1302.0)
    bg = L.background(os.path.join(W, 'isovist', 'Library_floor_plans.dxf'), WIN)
    gj = json.load(open(os.path.join(W, 'isovist', 'output', 'isovist_polygons_shelves_tall.geojson')))
    poly = {f['properties']['code']: np.array(f['geometry']['coordinates'][0]) for f in gj['features']}
    s = seats.merge(iso, on='code')
    cmap = LinearSegmentedColormap.from_list('blue', ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])
    norm = Normalize(s.isovist_area_m2.min(), s.isovist_area_m2.max())
    fig = plt.figure(figsize=(11, 8.9), facecolor=SURF); ax = fig.add_axes([0.01, 0.07, 0.98, 0.9]); ax.set_facecolor(SURF)
    for a in bg: ax.plot(a[:, 0], a[:, 1], color='#c9c8c3', lw=0.35, zorder=1)
    for t in L.TABLES: ax.add_patch(MplPoly(np.array(L.table_poly(*t[1:])), closed=True, fc='white', ec='#8a8984', lw=0.6, zorder=2))
    hi, lo = s.loc[s.isovist_area_m2.idxmax()], s.loc[s.isovist_area_m2.idxmin()]
    # two outline colours (18 Nov 2026, user request): orange = most open, green = most enclosed; solid vs dashed kept as a second cue
    OPEN_C, ENCL_C = '#eb6834', '#0f8a5f'
    for row, ls, colr in ((hi, '-', OPEN_C), (lo, '--', ENCL_C)):
        p = poly[row.code]; ax.add_patch(MplPoly(p, closed=True, fill=False, ec=colr, lw=1.6, ls=ls, zorder=4))
    took = set(v.seat)
    for row in s.itertuples():
        ax.add_patch(Rectangle((row.x_m - 0.3, row.y_m - 0.3), 0.6, 0.6, fc=cmap(norm(row.isovist_area_m2)), ec=SURF, lw=0.8, zorder=5))
        if row.code in took: ax.add_patch(Rectangle((row.x_m - 0.42, row.y_m - 0.42), 0.84, 0.84, fill=False, ec=INK, lw=0.9, zorder=6))
    for row, lab, colr in ((hi, 'most open', OPEN_C), (lo, 'most enclosed', ENCL_C)):
        right = row.x_m > (WIN[0] + WIN[1]) / 2                      # keep the label inside the frame
        ax.annotate(f'{row.code}: {row.isovist_area_m2:.0f} m² ({lab})', (row.x_m, row.y_m), xytext=(-12 if right else 12, -16),
                    textcoords='offset points', ha='right' if right else 'left', fontsize=8.5, color=INK, zorder=7,
                    bbox=dict(fc='white', ec=colr, lw=1.2, pad=2, alpha=0.95), arrowprops=dict(arrowstyle='-', color=colr, lw=1.0))
    ax.set_xlim(WIN[0], WIN[1]); ax.set_ylim(WIN[2], WIN[3]); ax.set_aspect('equal'); ax.axis('off')
    cax = fig.add_axes([0.06, 0.04, 0.35, 0.018])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation='horizontal')
    cb.set_label('Isovist area of the seat (m²)', fontsize=8.5, color=INK2); cb.ax.tick_params(labelsize=8, colors=INK2); cb.outline.set_visible(False)
    lg = fig.add_axes([0.45, 0.025, 0.54, 0.04]); lg.axis('off'); lg.set_xlim(0, 100); lg.set_ylim(0, 10)
    for x0, colr, ls, txt in ((0, OPEN_C, '-', 'Seen from the most open seat'), (36, ENCL_C, '--', 'Seen from the most enclosed seat')):
        lg.plot([x0, x0 + 5], [5, 5], color=colr, lw=2, ls=ls); lg.text(x0 + 6.5, 5, txt, va='center', fontsize=8.5, color=INK)
    lg.add_patch(Rectangle((74, 2.5), 2.2, 5, fill=False, ec=INK, lw=0.9)); lg.text(77.8, 5, 'Participant\'s seat', va='center', fontsize=8.5, color=INK)
    fig.savefig(os.path.join(FIG, 'openness_map.png'), dpi=220, facecolor=SURF); plt.close(fig)


if __name__ == '__main__':
    main()
