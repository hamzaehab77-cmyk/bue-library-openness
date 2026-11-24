"""Transcription of the behavioural-mapping sheets of 17 Nov 2026 (2 scans x 3 sheets, photos sent by the user).
Seat marks: S studying, P phone, T talking, O other, B belongings only, X chair missing, '' = chair there and empty.
Marks the transcriber could not read for certain are listed in UNSURE (value = best reading) and flagged in the CSV.
Extra chairs (not in the standard layout) are recorded per table in EXTRAS: (scan, table seats, count, activity).
usage: python transcribe_mapping_2026-11-17.py   -> writes behaviour_mapping_2026-11-17.csv and _extras.csv"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
seats = pd.read_csv(os.path.join(HERE, '..', 'drafts', 'figures', 'seat_codes_first_floor.csv'))

SCANS = {  # scan: sheet -> (start, end, observer)
    1: {1: ('14:00', '14:07', 'K.R'), 2: ('14:15', '14:24', '(initials crossed out)'), 3: ('14:25', '14:35', '[researcher]')},
    2: {1: ('16:14', '16:19', '[researcher]'), 2: ('16:20', '16:24', 'Hardy'), 3: ('16:16', '16:20', '[researcher]')},
}
SHEET_OF = lambda code: 1 if code[0] == 'A' or (code[0] == 'D' and int(code[2:]) <= 24) else (2 if code[0] in 'BC' else 3)


def marks(s):
    return dict(p.split('=') for p in s.split())


MARKS = {
    1: marks('A-1=X A-2=X A-9=X A-10=X A-3=X A-11=X A-4=S A-12=S A-5=X A-6=X A-13=X A-14=X A-7=X A-8=X A-15=X A-16=X '
             'A-17=T A-18=T A-25=T A-26=T A-19=T A-20=T A-27=T A-28=T A-21=B A-22=S A-29=S A-30=S '
             'A-23=X A-24=X A-31=X A-32=X '
             'D-1=X D-2=X D-8=X D-3=T D-9=T D-4=X D-10=X D-5=X D-6=X D-11=T D-12=T D-20=X '
             'D-15=X D-16=X D-21=X D-22=X D-17=X D-18=B D-23=X D-24=B '
             'B-13=S B-14=B B-5=X B-17=X B-18=X B-9=T B-10=T B-21=T B-22=T '
             'C-1=B C-2=S C-7=X C-8=S C-3=X C-4=S C-9=S C-10=S C-13=T C-14=T C-17=T C-18=T C-15=X C-16=X C-19=X C-20=X '
             'E-1=T E-2=B E-9=T E-10=X E-3=T E-11=T E-12=X E-5=X E-14=X E-7=X E-8=X E-15=X E-16=X '
             'E-17=X E-18=X E-25=X E-26=X E-19=X E-20=B E-27=X E-28=S E-21=S E-22=S E-29=S E-30=S '
             'E-24=B E-31=X E-33=S E-41=S E-35=T E-36=X E-43=T E-37=X E-38=X E-46=X '
             'E-39=T E-40=T E-47=S E-48=T D-25=B D-26=B D-27=S D-28=B'),
    2: marks('A-17=S A-32=S '
             'D-7=S D-8=S D-3=S D-4=S D-9=S D-10=S D-11=S D-12=S D-13=X D-14=S D-19=X D-20=X '
             'D-15=X D-16=X D-21=X D-17=S D-18=S D-23=S D-24=S '
             'B-1=X B-2=X B-13=S B-14=S B-17=X B-18=X B-19=S B-12=S C-6=X C-17=S '
             'E-1=B E-9=P E-3=X E-4=S E-12=S E-17=S E-25=X E-26=X E-20=B E-24=S '
             'E-33=S E-37=S E-45=S E-46=S E-40=P E-47=P E-43=P'),
}
# All unclear marks were confirmed by the user on 17 Nov 2026: [researcher]'s "d" = P; "~" at A-17 = S; D-25 = B;
# A-21 = B and A-22/29/30 = S; E-20 = B; scan 2 E-33 = S (chair moved in the direction of the arrow).
UNSURE = {}
GROUPS = {1: [['A-4', 'A-12'], ['A-17', 'A-18', 'A-25', 'A-26'], ['A-19', 'A-20', 'A-27', 'A-28'], ['A-21', 'A-22', 'A-29', 'A-30'],
              ['D-3', 'D-9'], ['D-11', 'D-12'], ['B-9', 'B-10', 'B-21', 'B-22'], ['E-39', 'E-40', 'E-47', 'E-48']],
          2: [['D-7', 'D-8'], ['D-3', 'D-4', 'D-9', 'D-10'], ['D-17', 'D-18', 'D-23', 'D-24'], ['E-1', 'E-9'], ['E-4', 'E-12'],
              ['E-37', 'E-45', 'E-46'], ['E-40', 'E-47']]}
EXTRAS = [  # scan, table (first seat), count, activity ('' = empty extra chair), note
    (1, 'A-5', 2, '', 'E/X x2 above table'), (1, 'A-7', 3, '', 'E/X x2 above, x1 below'),
    (1, 'A-17', 9, '', '9E/X, group with A-19 table'), (1, 'A-19', 5, '', '3E/X + 2E/X'), (1, 'A-23', 1, '', 'E/X'),
    (1, 'D-3', 1, 'T', 'E/T'), (1, 'D-17', 1, 'B', 'E/B'),
    (1, 'B-1', 3, '', '3E/X'), (1, 'B-3', 1, '', 'E/X'), (1, 'B-7', 2, '', 'E/X x2'),
    (1, 'B-9', 2, 'B', '2E/B'), (1, 'B-9', 1, 'T', 'E/T'),
    (1, 'B-11', 2, 'T', '2 people talking, sitting on the table (confirmed); its chairs empty'),
    (1, 'C-13', 5, 'T', '5E/T'),
    (1, 'E-21', 1, 'B', 'E/B'), (1, 'E-21', 4, 'S', '4E/S'), (1, 'E-21', 2, 'T (standing)', '2 standing talking'),
    (1, 'E-33', 1, 'S', 'extra S with arrow'), (1, 'E-35', 1, 'S', 'extra S with arrow'), (1, 'E-39', 1, 'T', 'E/T'),
    (1, 'D-25', 1, 'B', 'E/B'),
    (2, 'A-23', 1, 'S', 'E/S'), (2, 'D-5', 1, '', 'Ex'), (2, 'D-17', 1, 'S', 'E/S'),
    (2, 'B-1', 1, 'P', 'exP'), (2, 'B-7', 3, '', 'ex x3'), (2, 'B-9', 2, '', 'ex x2'), (2, 'B-11', 3, '', 'ex x3 (approx.)'),
    (2, 'E-17', 1, 'S', 'S with arrow next to E-18'), (2, 'D-25', 1, '', 'E/X'),
]
NOTES = ['Scan 1, area E (tables E-17 to E-28): "People studying here tend to be more focused" (observer note).',
         'Scan 2, D-7/D-8: "Drawing plans".', 'Scan 2 sheet 1: people counted = 11 (observer).',
         'Scan 1 sheet 1 (K.R) marks many chairs as missing (X) in A; scan 2 ([researcher]) marks none in A.']

rows = []
for scan, sheets in SCANS.items():
    gid = {c: f'G{scan}.{i + 1}' for i, g in enumerate(GROUPS[scan]) for c in g}
    for r in seats.itertuples():
        sh = SHEET_OF(r.code); start, end, obs = sheets[sh]
        m = MARKS[scan].get(r.code, '')
        rows.append(dict(date='2026-11-17', scan=scan, sheet=sh, start=start, end=end, observer=obs, seat=r.code, zone=r.zone,
                         mark=m, occupied=int(m in ('S', 'P', 'T', 'O', '?')), group=gid.get(r.code, ''),
                         unsure=UNSURE.get((scan, r.code), '')))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, 'behaviour_mapping_2026-11-17.csv'), index=False)
pd.DataFrame(EXTRAS, columns=['scan', 'table_first_seat', 'count', 'activity', 'note']).to_csv(
    os.path.join(HERE, 'behaviour_mapping_2026-11-17_extras.csv'), index=False)
with open(os.path.join(HERE, 'behaviour_mapping_2026-11-17_notes.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(NOTES) + '\n')

# summary
for scan in (1, 2):
    d = df[df.scan == scan]
    tab = d[d.mark != ''].pivot_table(index='zone', columns='mark', values='seat', aggfunc='count', fill_value=0)
    print(f'\nScan {scan}: standard seats by mark\n{tab}')
    ex = [e for e in EXTRAS if e[0] == scan]
    print('extra chairs with a person:', sum(e[2] or 0 for e in ex if e[3] and e[3] not in ('', '?')),
          '| extra empty chairs:', sum(e[2] or 0 for e in ex if e[3] == ''))
