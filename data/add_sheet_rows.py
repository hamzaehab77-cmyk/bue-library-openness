"""Add rows copied from the Google Sheet to data/responses.csv (and, optionally, exclusions to data/exclusions.csv).

usage: python add_sheet_rows.py <raw csv in data/raw> <length> <hash> [CODE|category|reason ...]

<length> and <hash> are computed in the browser on the exported sheet text of the same rows (rows joined by CRLF,
no header), so the copy is checked character by character before anything is written. The old responses.csv is
backed up in data/raw first. Used from 22 Nov 2026 (rows 67-73); the 48-66 batch used add_rows_2026-11-22.py."""
import os, shutil, sys, datetime
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(D)
raw = os.path.join(D, 'raw', sys.argv[1]); n_exp, h_exp = int(sys.argv[2]), int(sys.argv[3])

txt = open(raw, encoding='utf-8').read().rstrip('\n').split('\n', 1)[1].replace('\n', '\r\n')
h = 0
for c in txt: h = (h * 31 + ord(c)) % 1000000007
assert (len(txt), h) == (n_exp, h_exp), f'copy differs from the sheet: {(len(txt), h)}'

old = pd.read_csv(os.path.join(D, 'responses.csv'), dtype=str, keep_default_na=False)
new = pd.read_csv(raw, dtype=str, keep_default_na=False)
new['Seat code (as entered, old plan)'] = ''
dup = set(new['Response code']) & set(old['Response code']); assert not dup, f'rows already added: {dup}'
seats = set(pd.read_csv(os.path.join(W, 'drafts', 'figures', 'seat_codes_first_floor.csv')).code)
bad = sorted(set(new['Seat code']) - seats); assert not bad, f'unknown seat codes: {bad}'

stamp = datetime.date.today().isoformat()
bk = os.path.join(D, 'raw', f'responses_backup_{stamp}_before_{os.path.splitext(sys.argv[1])[0]}.csv')
if not os.path.exists(bk): shutil.copy(os.path.join(D, 'responses.csv'), bk)
pd.concat([old, new[old.columns]]).to_csv(os.path.join(D, 'responses.csv'), index=False, encoding='utf-8')

ex = pd.read_csv(os.path.join(D, 'exclusions.csv'), dtype=str, keep_default_na=False)
add = pd.DataFrame([a.split('|', 2) for a in sys.argv[4:]], columns=ex.columns)
ex = pd.concat([ex, add[~add.code.isin(ex.code)]]); ex.to_csv(os.path.join(D, 'exclusions.csv'), index=False)
print(f'responses.csv: {len(old)} -> {len(old) + len(new)} rows; exclusions: {len(ex)}')
