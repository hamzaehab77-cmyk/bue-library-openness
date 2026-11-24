"""Transcription of the whole-floor behavioural-mapping sheets v3 of 19 Nov 2026 (Thursday), from 4 photos sent by the user:
scan 1 (10:45-11:15) and scan 2 (12:00-12:30), each on sheet 1 (west: A + E) and sheet 2 (east: D, B, C).
Writes:
  behaviour_mapping_2026-11-19.csv         one row per standard seat per scan (same columns as 17 Nov + gender)
  behaviour_mapping_2026-11-19_extras.csv  people on extra chairs at a table
  behaviour_mapping_2026-11-19_people_off_seats.csv  people NOT on a chair at a table: standing, walking, sitting elsewhere
  behaviour_mapping_2026-11-19_notes.txt   the observers' written notes + main walking routes
Pen colour = gender, as corrected on the sheets: BLUE = male, BLACK = female, RED = cannot tell
([researcher] swapped blue/black for his walking LINES only; [researcher]'s lines follow the same key as her circles - observers, 24 Nov 2026).
Marks on the sheets: E = a moved/extra chair with a person on it, Ex or EE = an empty moved chair. 'unsure' = hard to read in the photo; the most likely reading was assumed (user, 20 Nov 2026). Researchers at D-25/D-26 ("us") are not counted.
Checked again on 24 Nov 2026 against [researcher]'s colour scans: D-1 in scan 2 is blue (male), not black; staff desk added."""
import os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W, 'isovist'))
import standard_layout as L

DATE = '2026-11-19'
SCANS = {1: {1: ('10:45', '11:15', '[researcher]'), 2: ('10:45', '11:15', '[researcher]')},
         2: {1: ('12:00', '12:30', '[researcher]'), 2: ('12:00', '12:25', '[researcher]')}}
SHEET_OF = lambda code: 1 if code[0] in 'AE' else 2

# seat: (letter, gender M/F/U). X = chair missing. Unmarked seats = chair there, empty.
MARKS = {
    1: {  # ---- scan 1, 10:45-11:15
        'D-3': ('S', 'M'), 'D-11': ('S', 'F'), 'D-1': ('T', 'U'), 'D-2': ('T', 'U'), 'D-7': ('T', 'U'), 'D-8': ('T', 'U'),
        'D-13': ('P', 'F'), 'D-15': ('S', 'M'), 'D-21': ('S', 'M'), 'D-23': ('P', 'M'),
        'B-14': ('S', 'F'), 'B-3': ('P', 'F'), 'B-4': ('T', 'F'), 'B-15': ('T', 'F'), 'B-5': ('S', 'F'), 'B-6': ('S', 'F'),
        'B-17': ('S', 'F'), 'B-20': ('S', 'F'), 'B-9': ('S', 'F'), 'B-21': ('S', 'F'), 'B-11': ('T', 'M'), 'B-12': ('T', 'M'),
        'C-1': ('T', 'F'), 'C-7': ('T', 'F'), 'C-2': ('T', 'M'), 'C-8': ('T', 'M'), 'C-14': ('X', ''), 'C-17': ('S', 'M'),
        'A-2': ('S', 'F'), 'A-10': ('S', 'F'), 'A-4': ('S', 'F'), 'A-8': ('S', 'M'), 'A-16': ('S', 'M'), 'A-26': ('S', 'F'),
        'E-1': ('S', 'F'), 'E-9': ('S', 'F'), 'E-2': ('X', ''), 'E-12': ('S', 'F'), 'E-17': ('P', 'F'), 'E-21': ('P', 'M'),
        'E-24': ('S', 'F'), 'E-32': ('S', 'F'), 'E-31': ('X', ''), 'E-34': ('S', 'F'), 'E-41': ('S', 'F'), 'E-42': ('S', 'F'),
        'E-35': ('S', 'F'), 'E-43': ('P', 'F'), 'E-44': ('P', 'M'), 'E-40': ('S', 'M'), 'E-48': ('S', 'M')},
    2: {  # ---- scan 2, 12:00-12:30
        'D-1': ('T', 'M'), 'D-2': ('S', 'F'), 'D-8': ('T', 'F'), 'D-3': ('S', 'F'), 'D-6': ('S', 'F'), 'D-12': ('S', 'F'),
        'D-13': ('S', 'F'), 'D-17': ('T', 'F'), 'D-23': ('P', 'F'),
        'B-1': ('S', 'U'), 'B-2': ('S', 'U'), 'B-15': ('T', 'F'), 'B-16': ('T', 'F'), 'B-5': ('S', 'F'), 'B-6': ('S', 'F'),
        'B-18': ('S', 'F'), 'B-8': ('S', 'F'), 'B-9': ('S', 'F'), 'B-21': ('S', 'F'),
        'C-1': ('T', 'F'), 'C-2': ('T', 'F'), 'C-3': ('X', ''), 'C-4': ('X', ''), 'C-9': ('X', ''), 'C-10': ('X', ''),
        'C-6': ('S', 'F'), 'C-12': ('S', 'F'), 'C-17': ('S', 'M'), 'C-15': ('B', ''), 'C-19': ('X', ''), 'C-20': ('S', 'M'),
        'A-1': ('T', 'M'), 'A-2': ('T', 'M'), 'A-10': ('T', 'M'), 'A-4': ('S', 'F'), 'A-12': ('S', 'F'), 'A-5': ('T', 'F'),
        'A-6': ('S', 'F'), 'A-14': ('T', 'F'), 'A-8': ('P', 'M'), 'A-16': ('S', 'M'), 'A-19': ('T', 'F'), 'A-28': ('T', 'M'),
        'A-30': ('S', 'F'),
        'E-9': ('S', 'M'), 'E-4': ('P', 'M'), 'E-7': ('B', ''), 'E-17': ('T', 'F'), 'E-25': ('T', 'F'), 'E-28': ('S', 'F'),
        'E-22': ('P', 'M'), 'E-24': ('P', 'F'), 'E-32': ('T', 'F'), 'E-31': ('X', ''), 'E-37': ('P', 'F'), 'E-38': ('T', 'F'),
        'E-45': ('T', 'F'), 'E-46': ('S', 'F'), 'E-40': ('S', 'M'), 'E-48': ('S', 'M'), 'E-33': ('S', 'F'), 'E-34': ('B', ''),
        'E-41': ('B', ''), 'E-42': ('B', ''), 'E-35': ('P', 'F'), 'E-36': ('P', 'F'), 'E-43': ('T', 'F'), 'E-44': ('P', 'M')}}

GROUPS = {1: [['D-1', 'D-2', 'D-7', 'D-8'], ['C-1', 'C-2', 'C-7', 'C-8'], ['E-24', 'E-32'], ['E-34', 'E-41', 'E-42'], ['E-40', 'E-48']],
          2: [['A-1', 'A-2', 'A-10'], ['A-5', 'A-6', 'A-14'], ['A-19', 'A-28'], ['C-1', 'C-2'], ['E-33', 'E-34', 'E-41', 'E-42'],
              ['E-35', 'E-36', 'E-43', 'E-44']]}

UNSURE = {(1, 'D-1'): 'group of 8 drawn in the void next to table D-1/2/7/8, "all talking"; this group got up and a new group sat in its place',
          (1, 'D-2'): 'same group', (1, 'D-7'): 'same group', (1, 'D-8'): 'same group',
          (1, 'D-21'): 'pen colour', (1, 'D-23'): 'filled blue dot with an arrow to a P symbol in the void',
          (1, 'C-2'): 'E = person on a moved chair at this spot; activity assumed T (part of the talking group around C-1)', (1, 'C-8'): 'as C-2',
          (1, 'A-16'): 'faint symbol', (2, 'D-8'): 'pen colour', (2, 'D-17'): 'letter unclear ("joined later")',
          (2, 'B-1'): 'pen colour', (2, 'B-2'): 'pen colour', (2, 'C-6'): 'plain S without a circle', (2, 'C-12'): 'plain S without a circle',
          (2, 'A-8'): 'letter unclear (P?)', (2, 'A-16'): 'letter unclear (S?)', (2, 'E-4'): 'letter unclear (P?)',
          (2, 'E-7'): 'heart-shaped mark, read as B', (2, 'E-41'): 'heart-shaped mark, read as B', (2, 'E-42'): 'heart-shaped mark, read as B',
          (2, 'E-45'): 'letter unclear (T?)'}

EXTRAS = [  # scan, table (first seat), count, activity, gender note, note
    (1, 'D-1', 4, 'T', '', 'group of 8 around D-1/2/7/8: 4 on the standard chairs + 4 on extra chairs'),
    (1, 'D-17', 1, 'T', '', '"extra talking" next to D-17 (unsure)'),
    (1, 'C-1', 1, 'P', 'F', 'extra chair at the end of table C-1'),
    (2, 'C-1', 2, 'T', 'F', 'two extra chairs at the top end of table C-1'),
    (2, 'C-1', 2, '', '', 'two empty moved chairs (Ex) below table C-1'),
    (2, 'B-3', 1, 'P', 'F', 'extra chair between B-16 and B-17'),
    (2, 'C-13', 1, 'S', 'F', 'extra chair below table C-13')]

OFF = [  # scan, sheet, area, posture (stand / walk / sit_other = on a chair away from a table / sit_else = floor, ledge), activity,
         # gender, staff (1 = staff or visitor), count, where, note
    (1, 2, 'B', 'stand', '', 'U', 0, 2, 'between B-1 table and the bookshelves', ''),
    (1, 2, 'D', 'stand', '', 'U', 0, 1, 'corridor south of D, next to the researchers', ''),
    (1, 2, 'C', 'stand', '', 'U', 0, 1, 'next to the east stairs', ''),
    (1, 2, 'D', 'walk', '', 'U', 1, 1, 'corridor south of D', '"Supervisor walking here"'),
    (1, 2, 'C', 'walk', '', 'U', 0, 1, 'corridor towards the east stairs', '"Running?"'),
    (1, 1, 'A', 'stand', 'P', 'U', 0, 2, 'between the west bookshelves', '"People on the phone between the shelves"'),
    (1, 1, 'A', 'walk', '', 'U', 1, 1, 'north of A', '"Staff moving chairs outside"'),
    (1, 1, 'A', 'stand', 'S', 'U', 0, 1, 'next to table A-19', 'standing while studying (unsure)'),
    (1, 1, 'A', 'stand', '', 'U', 1, 1, 'east of A, near the shelves', '"Staff member"'),
    (1, 1, 'E', 'walk', '', 'F', 0, 1, 'from the door through E', 'walked in, dropped her belongings, went to the toilet, came back, '
                                                                     'kept walking around to pick a seat: wanted a table near a charger'),
    (2, 2, 'D', 'sit_other', 'S', 'U', 0, 1, 'corridor south of D, on a chair away from a table', ''),
    (2, 2, 'D', 'sit_other', 'S', 'U', 0, 1, 'single desk and chair at the south-west corner of D (not in the plan)',
     '"There is a chair and a desk here but singular"'),
    (2, 2, 'D', 'stand', 'T', 'U', 0, 1, 'next to the researchers\' table D-25', ''),
    (2, 2, 'B', 'stand', '', 'M', 0, 2, 'next to table B-1', ''),
    (2, 2, 'C', 'walk', '', 'U', 1, 1, 'corridor south of C', '"Supervisor"'),
    (2, 1, 'A', 'stand', '', 'U', 0, 1, 'next to table A-1', ''),
    (2, 1, 'A', 'stand', '', 'U', 0, 1, 'north of table A-5', ''),
    (2, 1, 'A', 'stand', 'T', 'U', 0, 4, 'south of A, at the information desk', '"People asking for something from staff: they want to book a '
                                                                              'study room"; "two girls walked to the info desk, then went back"'),
    (2, 1, 'A', 'sit_other', 'O', 'U', 1, 1, 'information desk, south-east of A', '"Staff member"'),
    (2, 1, 'A', 'stand', 'L', 'U', 0, 2, 'between the west bookshelves', '"Two people looking for books"; "4 of them kept going back"'),
    (2, 1, 'E', 'stand', '', 'U', 0, 2, 'next to tables E-17 and E-25', ''),
    (2, 1, 'E', 'stand', 'T', 'F', 0, 1, 'next to table E-43', '"The girl sat but kept talking"'),
    # 24 Nov observer note for all maps: a staff member is always at the staff desk by the east stairs (not drawn on 19 Nov)
    (1, 2, 'C', 'sit_other', 'O', 'F', 1, 1, 'staff desk by the east stairs, south of C', 'added from the 24 Nov note "she is always here for all maps"'),
    (2, 2, 'C', 'sit_other', 'O', 'F', 1, 1, 'staff desk by the east stairs, south of C', 'added from the 24 Nov note "she is always here for all maps"')]

NOTES = [
    'MAIN WALKING ROUTES (drawn as lines, both scans): (1) the east-west corridor between the south row of D and area C, towards the '
    'east stairs - the busiest route on the floor; (2) the north corridor along the rooms, in front of the first rows of D and B; '
    '(3) the north-south link between areas A/E and D, from the library entrance (main door at the north-east corner of A) to E, the '
    'toilets and the information desk; (4) loops around the tables of A and E by students looking for a seat.',
    'Scan 1 east: "People in this room are working with clay or something related to dentistry, then moved to the bathroom to wash their '
    'hands" (enclosed room north of B; not part of the study area).',
    'Scan 1 east: "This group got up and a new group sat in their place" (D-1/2/7/8, all talking).',
    'Scan 1 east: "All tables with people are together" (people sitting at a table are one group).',
    'Scan 1 west: a student walked in, dropped her belongings, went to the toilet, came back and kept walking around; asked, she said she '
    'was looking for a table near a charger.',
    'Scan 2 east: D-3 got up at 12:22; a student who sat from 11:00 got up at 12:10; "Drawing and modelling" in the room north of B; '
    '"took a pic"; a student got up to ask others for help with internet issues; "More people are leaving now" (end of scan 2).',
    'Scan 2 west: "People who left belongings came back" (E-33 to E-42); "the girl sat but kept talking" (E-43); "talking while looking at '
    'laptop / studying" (E-35 to E-44); people entering by the main door; students asking staff at the information desk to book a study room.',
    'Pen colours: blue = male, black = female, red = cannot tell (key corrected on the sheets); the observers swapped blue and black for the '
    'walking lines only.',
    'Gender (user, 24 Nov 2026): the observers did not use "cannot tell"; marks that were unclear on these sheets have their gender '
    'estimated from the female/male ratio recorded in the other whole-floor scans (column gender_estimated = 1).']

seats = L.build()
rows = []
for scan, sheets in SCANS.items():
    gid = {c: f'G{scan}.{i + 1}' for i, g in enumerate(GROUPS[scan]) for c in g}
    for r in seats.itertuples():
        sh = SHEET_OF(r.code); start, end, obs = sheets[sh]
        m, g = MARKS[scan].get(r.code, ('', ''))
        if (scan, r.code) not in UNSURE and r.code in ('D-25', 'D-26'): pass
        rows.append(dict(date=DATE, scan=scan, sheet=sh, start=start, end=end, observer=obs, seat=r.code, zone=r.zone, mark=m,
                         occupied=int(m in ('S', 'T', 'P', 'O', 'L')), gender=g, group=gid.get(r.code, ''),
                         unsure=UNSURE.get((scan, r.code), '')))
out = pd.DataFrame(rows)
for (scan, code) in [(1, 'D-25'), (1, 'D-26'), (2, 'D-25'), (2, 'D-26')]:          # researchers' own seats: not observed
    out.loc[(out.scan == scan) & (out.seat == code), 'unsure'] = 'researchers sitting here ("us"), not counted'
bad = [k for s in MARKS for k in MARKS[s] if k not in set(seats.code)]
assert not bad, bad
# ---- gender (user, 24 Nov 2026): the observers did not use "cannot tell"; marks read as unclear on these older sheets are
# ESTIMATED from the female/male ratio recorded in the other whole-floor scans (19 and 24 Nov), and flagged gender_estimated = 1.
ex_df = pd.DataFrame(EXTRAS, columns=['scan', 'table_first_seat', 'count', 'activity', 'gender', 'note'])
off_df = pd.DataFrame(OFF, columns=['scan', 'sheet', 'area', 'posture', 'activity', 'gender', 'staff', 'count', 'where', 'note'])
rec = {'F': 0, 'M': 0}
for g in ('F', 'M'):
    rec[g] += int(((out.occupied == 1) & (out.gender == g)).sum()) + int(ex_df[ex_df.gender == g]['count'].sum()) + int(off_df[off_df.gender == g]['count'].sum())
f24 = os.path.join(HERE, 'behaviour_mapping_2026-11-24.csv')
if os.path.exists(f24):
    s24 = pd.read_csv(f24, keep_default_na=False)
    e24 = pd.read_csv(f24.replace('.csv', '_extras.csv'), keep_default_na=False)
    o24 = pd.read_csv(f24.replace('.csv', '_people_off_seats.csv'), keep_default_na=False)
    for g in ('F', 'M'):
        rec[g] += int(((s24.occupied == 1) & (s24.gender == g)).sum()) + int(e24[e24.gender == g]['count'].sum()) + int(o24[o24.gender == g]['count'].sum())
P_F = rec['F'] / (rec['F'] + rec['M'])
out['gender_estimated'] = 0
for scan in SCANS:
    idx = out[(out.scan == scan) & (out.occupied == 1) & ~out.gender.isin(['M', 'F'])].sort_values('seat').index
    n_f = int(round(len(idx) * P_F))
    out.loc[idx[:n_f], 'gender'] = 'F'; out.loc[idx[n_f:], 'gender'] = 'M'; out.loc[idx, 'gender_estimated'] = 1


def split_rows(df):
    """per scan: all people of unclear gender together get round(n * P_F) females, the rest males (rows split if needed)"""
    rows = []
    for scan, g_ in df.groupby('scan', sort=True):
        recs = g_.to_dict('records')
        todo = [r for r in recs if not (r['gender'] in ('M', 'F') or int(r['count']) == 0 or
                                        (r.get('activity', 'x') == '' and 'table_first_seat' in r))]
        left_f = int(round(sum(int(r['count']) for r in todo) * P_F))
        for r in recs:
            if r not in todo: rows.append({**r, 'gender_estimated': 0}); continue
            k_f = min(left_f, int(r['count'])); left_f -= k_f
            for g, k in (('F', k_f), ('M', int(r['count']) - k_f)):
                if k: rows.append({**r, 'gender': g, 'count': k, 'gender_estimated': 1})
    return pd.DataFrame(rows)


ex_df, off_df = split_rows(ex_df), split_rows(off_df)
print(f'gender estimate: female share {P_F:.2f} from {rec["F"] + rec["M"]} people with a recorded gender')
out.to_csv(os.path.join(HERE, f'behaviour_mapping_{DATE}.csv'), index=False)
ex_df.to_csv(os.path.join(HERE, f'behaviour_mapping_{DATE}_extras.csv'), index=False)
off_df.to_csv(os.path.join(HERE, f'behaviour_mapping_{DATE}_people_off_seats.csv'), index=False)
open(os.path.join(HERE, f'behaviour_mapping_{DATE}_notes.txt'), 'w', encoding='utf-8').write('\n\n'.join(NOTES))
for s in (1, 2):
    q = out[out.scan == s]
    print(f'scan {s}:', q[q.mark != ''].mark.value_counts().to_dict(), '| unsure', int((q.unsure != '').sum()))
