"""Transcription of the whole-floor behavioural-mapping sheets v3 of 24 Nov 2026 (Tuesday), last mapping day.
Sheets numbered 3, 4 and 5 by the observers (continuing from 19 Nov) = scans 1, 2 and 3 of this day:
  scan 1 = sheet scan 3, 10:00-10:35; scan 2 = sheet scan 4, 12:00-12:30; scan 3 = sheet scan 5, 13:30-14:00.
EAST half (areas D, B, C; observer [researcher]) from 'hamzas behavioral map .pdf' (colour scans) + photos.
WEST half (areas A, E; observer [researcher]): TO ADD when the colour photos of her sheets arrive (her PDF scans are greyscale).
Pen colour on 24 Nov (key corrected on sheet scan 3, "check this for all maps"): BLACK = male, RED = female, BLUE = cannot tell.
Observer notes applied to all maps: people sitting at the same table are one group; a staff member is always at the staff
desk by the east stairs (south of C). Some walking arrows stand for a group ("group of 3", "5 people").
The extra 'seating only at 2:00' sheet of scan 5 is a second look at the seats after people started leaving at 13:55;
it is kept in the notes, not as a separate scan (it would count the same people twice).
Writes behaviour_mapping_2026-11-24.csv / _extras.csv / _people_off_seats.csv / _notes.txt (same columns as 19 Nov)."""
import os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W, 'isovist'))
import standard_layout as L

DATE = '2026-11-24'
SCANS = {1: {1: ('10:00', '10:35', '[researcher]'), 2: ('10:00', '10:35', '[researcher]')},
         2: {1: ('12:00', '12:30', '[researcher]'), 2: ('12:00', '12:30', '[researcher]')},
         3: {1: ('13:30', '14:00', '[researcher]'), 2: ('13:30', '14:00', '[researcher]')}}
SHEET_SCAN_NO = {1: 3, 2: 4, 3: 5}
SIDES_DONE = {1, 2}                  # 1 = west (A, E), 2 = east (D, B, C)
# WEST ([researcher]), from her colour photos (24 Nov, 18:24). Key on her 24 Nov sheets as printed: BLUE = male, RED = female,
# BLACK = cannot tell. Mark U = a person is there but the letter cannot be read (occupied, activity unknown).
WEST = {
    1: 'A-1=P/M A-9=P/M A-2=S/F A-10=S/M A-4=T/M A-11=S/F A-12=S/F A-6=P/F A-14=P/F A-13=X A-8=T/F A-16=T/F '
       'A-17=S/F A-18=S/F A-25=S/F A-26=X A-19=P/M A-27=P/M A-28=S/F A-21=P/F A-29=T/F A-22=X A-30=X A-31=P/M A-32=P/F '
       'E-2=S/M E-10=S/M E-4=S/F E-12=S/M E-5=S/M E-6=S/F E-14=S/F E-15=X E-18=S/M E-25=S/M E-19=T/M E-20=P/M E-27=T/M '
       'E-28=P/M E-21=T/M E-29=S/F E-30=S/F E-24=T/M E-32=S/F E-33=T/F E-36=S/F E-44=S/M E-37=P/F E-45=P/F E-40=T/F E-47=S/F',
    2: 'A-1=X A-2=X A-10=X A-3=X A-11=X A-12=X A-4=T/F A-6=S/F A-7=X A-8=S/F A-15=S/F A-16=S/F A-17=T/F A-25=T/F A-18=X '
       'A-26=P/F A-19=T/M A-27=T/M A-22=P/M A-29=P/M A-30=P/F A-23=X A-24=P/F A-31=P/F A-32=P/F '
       'E-1=X E-9=X E-2=S/F E-10=S/F E-3=S/M E-11=B E-4=X E-12=X E-5=S/F E-13=X E-6=X E-14=X E-19=S/F E-27=S/F E-21=T/M '
       'E-29=T/M E-22=S/M E-30=S/M E-23=T/M E-24=P/M E-31=T/M E-32=T/M E-25=S/M E-33=P/F E-41=B E-35=X E-43=S/M E-37=S/F '
       'E-45=P/F E-38=S/F E-39=X E-47=S/M E-40=X E-48=X',
    3: 'A-1=T/F A-2=T/F A-9=T/F A-10=T/F A-3=P/F A-4=P/F A-11=T/F A-5=T/M A-13=T/M A-6=T/M A-14=T/F A-7=S/F A-15=P/F '
       'A-8=S/F A-16=S/F A-17=S/F A-18=S/F A-25=S/F A-26=X A-19=X A-20=X A-27=S/F A-28=X A-29=T/F A-24=P/F '
       'E-1=X E-9=X E-2=S/F E-3=B E-11=O/M E-4=X E-12=X E-5=X E-13=X E-14=X E-15=X E-16=X E-19=P/F E-27=P/F E-22=T/M '
       'E-30=T/M E-23=P/M E-24=T/F E-31=X E-32=T/F E-33=X E-34=X E-41=B E-42=X E-35=X E-43=X E-36=P/M E-44=O/F E-37=B '
       'E-45=B E-38=B E-46=B E-40=P/M E-48=P/M'}
SHEET_OF = lambda code: 1 if code[0] in 'AE' else 2


def M(s):
    """'D-2=T/F D-7=X ...' -> {seat: (letter, gender)}"""
    out = {}
    for p in s.split():
        k, v = p.split('=')
        l, g = (v.split('/') + [''])[:2]
        out[k] = (l, g)
    return out


MARKS = {
    1: M('D-2=T/F D-8=T/M D-7=S/F D-4=S/M D-10=O/M D-12=S/F D-14=S/M D-20=S/M D-15=S/M D-21=S/M D-17=S/M D-23=S/M D-18=S/F '
         'D-24=S/F D-27=S/F D-28=S/F '
         'B-14=P/M B-3=P/F B-4=O/F B-17=S/F B-8=B B-9=X B-10=X B-21=P/F B-11=S/M B-12=S/M B-23=S/M B-24=S/M '
         'C-1=S/M C-3=T/M C-9=T/M C-10=P/F C-12=S/M C-13=O/M C-17=P/M C-15=S/M C-19=S/F'),
    2: M('D-1=T/F D-2=T/F D-7=X D-8=T/F D-3=S/F D-9=S/F D-4=S/M D-10=S/M D-5=X D-6=X D-11=X D-12=P/M '
         'D-13=T/M D-14=T/M D-15=T/F D-16=T/F D-21=T/F D-22=T/F D-18=T/M D-24=P/M D-25=S/F D-26=T/F D-27=S/F D-28=S/M '
         'B-1=T/M B-2=T/F B-13=X B-14=X B-3=T/F B-4=T/F B-16=S/F B-5=S/M B-6=S/M B-17=X B-18=B B-7=T/M B-8=T/M B-19=T/M B-20=S/M '
         'B-9=X B-10=S/F B-21=X B-22=X B-23=B B-24=B '
         'C-1=X C-2=T/F C-7=P/F C-8=T/F C-4=S/F C-11=P/F C-6=S/F C-12=P/F C-14=P/M C-17=P/F C-18=S/F C-15=B C-19=B'),
    3: M('D-1=X D-7=X D-2=T/M D-8=T/M D-3=T/F D-4=S/F D-9=X D-10=B D-5=X D-6=X D-11=X D-12=X '
         'D-13=T/M D-14=T/M D-15=T/F D-21=T/F D-22=T/F D-17=X D-18=O/M D-23=T/M D-24=S/M D-25=S/M D-26=S/M D-28=S/M '
         'B-1=B B-2=S/F B-13=X B-14=X B-3=X B-4=X B-15=S/F B-16=S/F B-5=S/M B-6=T/M B-17=X B-18=X B-7=X B-19=S/M '
         'B-9=X B-10=S/F B-21=S/F B-22=S/F B-11=T/M B-12=T/F '
         'C-1=T/F C-2=T/F C-7=T/F C-8=T/F C-3=X C-4=S/F C-5=S/F C-6=X C-11=X C-12=X C-13=T/F C-14=P/M C-17=T/F C-18=P/M '
         'C-15=T/F C-16=T/F C-19=T/F C-20=T/F')}

for _s, _m in WEST.items(): MARKS[_s].update(M(_m))

# [researcher], sheet scan 5 (= scan 3 here): the seats inside the box drawn round the tables of area A were marked mirrored on both
# axes ("mirror it on x & y axis so the corner goes to its exact opposite corner"). Answers were given in the numbering as drawn,
# so they are entered as drawn above and then flipped: A-n -> A-(33-n) (A-1..A-32 = 4 rows x 8 seats). Only the standard seats
# move; extra chairs, walking lines and notes around them are correct as drawn (observer, 24 Nov 2026).
FLIP = lambda c: f'A-{33 - int(c[2:])}'
MARKS[3] = {(FLIP(k) if k[0] == 'A' else k): v for k, v in MARKS[3].items()}

C = 'clarified by the observer 24 Nov: '
UNSURE = {(1, 'A-1'): C + 'P, blue', (1, 'A-9'): C + 'P, blue', (1, 'A-10'): C + 'blue (male)', (1, 'A-4'): C + 'T, blue (male)',
          (1, 'A-31'): 'next to people on moved chairs; "girl grabbed a chair from another table, talking on the phone"',
          (1, 'E-21'): C + 'T', (1, 'E-32'): C + 'S, red; left the library afterwards', (1, 'E-44'): C + 'S, blue (male)',
          (2, 'A-26'): C + 'P', (2, 'A-30'): C + 'P', (2, 'A-24'): C + 'P', (2, 'A-31'): C + 'P',
          (2, 'A-32'): C + '"P as in missing chair" (entered as P)', (2, 'E-27'): C + 'S', (2, 'E-25'): C + 'S, blue (male)',
          (2, 'E-40'): C + 'X, chair missing', (2, 'E-3'): '"guy came and sat studying"',
          (3, 'E-2'): C + 'S, red (female)', (3, 'E-32'): C + 'T', (3, 'E-44'): C + 'O (sleeping)', (3, 'E-11'): C + 'O'}
UNSURE.update({(3, FLIP(k)): 'seat marked mirrored on the sheet (drawn at ' + k + '); ' + v for k, v in {
    'A-1': '"all talking together" (table drawn at A-1)', 'A-13': C + 'T, blue', 'A-15': C + 'P', 'A-24': C + 'P'}.items()})
UNSURE.update({(1, 'B-11'): '"W" written in the circles; key on the sheet: W = S, "talking while working on laptop" (all four + 2 extras)',
          (1, 'B-12'): 'as B-11', (1, 'B-23'): 'as B-11', (1, 'B-24'): 'as B-11',
          (1, 'D-2'): 'group note: "big group mainly talking but studying too because they have laptops on"',
          (1, 'D-8'): 'as D-2', (1, 'D-7'): 'as D-2',
          (1, 'D-17'): 'blue circle "talking about work" around this table (S kept)', (1, 'D-18'): 'as D-17',
          (1, 'D-23'): 'as D-17', (1, 'D-24'): 'as D-17', (1, 'D-27'): '"came later"', (1, 'D-28'): '"came later"',
          (2, 'B-3'): C + 'table hatched over; the correct marks are drawn above it: B-3 T red, B-4 T red, B-16 S red',
          (2, 'B-4'): 'as B-3', (2, 'B-16'): 'as B-3', (2, 'C-2'): C + 'T, red', (2, 'C-7'): C + 'P, red', (2, 'C-8'): C + 'T, red',
          (2, 'D-3'): '"They were a big group discussing a presentation they have; got up 12:15"', (2, 'D-9'): 'as D-3',
          (2, 'D-4'): 'as D-3', (2, 'D-10'): 'as D-3',
          (3, 'C-17'): C + 'red circle, T (female, talking)', (3, 'D-18'): C + 'sleeping (O)'})

EXTRAS = [  # scan, table (first seat), count, activity, gender, note
    (1, 'D-1', 1, 'T', 'F', 'extra chair north of table D-1/2/7/8 (big group)'),
    (1, 'D-1', 1, 'T', 'M', 'extra chair north of table D-1/2/7/8 (big group)'),
    (1, 'D-13', 1, 'S', 'M', 'extra chair below D-20'),
    (1, 'B-11', 2, 'S', 'M', 'two extra chairs on the west end of table B-11 ("W" = studying while talking)'),
    (2, 'D-3', 1, 'S', 'F', 'extra chair north of table D-3 (presentation group)'),
    (2, 'D-3', 1, 'S', 'M', 'extra chair north of table D-3 (presentation group)'),
    (2, 'D-13', 1, 'T', 'M', 'extra chair north of table D-13'),
    (2, 'D-17', 2, 'T', 'M', 'two extra chairs east of table D-17/18/23/24'),
    (2, 'D-25', 1, 'S', 'M', 'extra chair west of table D-25'),
    (2, 'D-25', 1, 'S', 'F', 'extra chair south of table D-25'),
    (2, 'B-7', 1, 'T', 'M', 'extra chair west of table B-7'),
    (2, 'C-3', 1, 'S', 'F', 'extra chair north of table C-3'),
    (2, 'B-11', 1, '', '', '"EB": extra chair with belongings, west of table B-11'),
    (3, 'D-3', 1, 'P', 'F', 'extra chair north of table D-3'),
    (3, 'D-3', 1, 'T', 'F', 'extra chair north of table D-3'),
    (3, 'D-13', 1, 'T', 'M', 'extra chair north of table D-13'),
    (3, 'D-17', 2, 'T', 'M', 'two extra chairs east and south of table D-17'),
    (3, 'B-3', 1, 'P', 'M', 'extra chair between tables B-3 and B-5'),
    (3, 'B-7', 1, '', '', '"Ex": empty extra chair west of table B-7'),
    (3, 'D-25', 1, '', '', '"EX": empty extra chair south of table D-25'),
    (3, 'C-3', 1, 'S', 'F', 'extra chair north of table C-3'),
    (3, 'C-5', 1, 'S', 'F', 'extra chair north of table C-5'),
    (3, 'C-13', 3, 'T', 'F', 'three extra chairs around table C-13 (north T F, west T F, south P M)')]

EXTRAS += [  # west ([researcher])
    (1, 'A-1', 2, '', '', 'two empty extra chairs north of table A-1 ("grabbed chairs from other tables"; observer: no one sitting)'),
    (1, 'A-3', 1, 'T', 'F', 'extra chair north of table A-3'),
    (1, 'A-17', 1, 'P', 'F', 'extra chair west of A-25: "girl sat on her phone then left"'),
    (1, 'A-21', 1, 'T', 'M', 'extra chair south of table A-21'),
    (1, 'A-23', 2, 'T', 'F', 'moved chairs west of table A-23: two females (red) who sat here after the first person (male) left'),
    (1, 'A-23', 1, 'S', 'F', 'extra chair south of A-32 (crossed out on the sheet)'),
    (1, 'E-19', 3, 'T', 'M', 'three extra chairs around table E-19 (two north T, one south P), all male'),
    (1, 'E-21', 1, 'P', 'M', 'extra chair south of table E-21'),
    (1, 'E-33', 1, 'T', 'F', 'extra chair north of table E-33 (group of three)'),
    (1, 'E-33', 1, 'T', 'M', 'extra chair south-west of table E-33 (group of three)'),
    (1, 'E-35', 1, 'T', 'F', 'extra chair south of table E-35: "girl keeps moving around the table"'),
    (2, 'A-3', 1, 'T', 'M', 'extra chair north of table A-3'),
    (2, 'A-5', 1, 'P', 'F', 'extra chair north of table A-5'),
    (2, 'A-17', 1, 'T', 'F', 'extra chair north of table A-17'),
    (2, 'A-19', 1, 'T', 'F', 'extra chair north of table A-19'),
    (2, 'A-21', 1, 'T', 'F', 'extra chair south of table A-21'),
    (2, 'A-23', 1, 'P', 'F', 'extra chair south of table A-23'),
    (2, 'E-19', 2, 'S', 'F', 'extra chairs around table E-19'),
    (2, 'E-19', 1, 'P', 'F', 'extra chair at table E-19, next to the empty one'),
    (2, 'E-19', 1, '', '', '"ex" in the circle: empty extra chair at table E-19'),
    (2, 'E-21', 2, 'S', 'M', 'extra chairs north of table E-21 ("studying together", later "they were all talking")'),
    (2, 'E-23', 1, 'P', 'M', 'extra chair south of table E-23'),
    (3, 'A-1', 3, 'T', 'F', '"all talking together": three extra chairs at table A-1'),
    (3, 'A-3', 1, 'P', 'F', 'extra chair north of table A-3'),
    (3, 'A-3', 1, 'T', 'M', 'extra chair south of table A-3'),
    (3, 'A-3', 1, 'T', 'F', 'extra chair south of table A-3'),
    (3, 'A-3', 1, 'T', 'F', 'extra chair south of table A-3'),
    (3, 'A-5', 1, 'T', 'F', 'extra chair north of table A-5'),
    (3, 'A-5', 1, 'T', 'M', 'extra chair north of table A-5'),
    (3, 'A-21', 1, 'T', 'M', 'extra chair south of table A-21'),
    (3, 'A-23', 2, 'T', 'F', 'extra chairs around table A-23 (red)'),
    (3, 'A-23', 2, '', '', '"ex": two empty extra chairs around table A-23'),
    (3, 'A-23', 1, 'U', 'M', 'extra chair south of table A-23 (blue), letter unclear'),
    (3, 'E-5', 1, 'P', 'M', 'extra chair north of table E-5'),
    (3, 'E-17', 2, '', '', '"ex": two empty extra chairs north of table E-17; "2 people left the table"'),
    (3, 'E-19', 2, 'T', 'F', 'extra chairs west and south of table E-19'),
    (3, 'E-23', 1, 'S', 'F', 'extra chair at table E-23'),
    (3, 'E-23', 1, 'T', 'F', 'extra chair at table E-23')]

STAFF_DESK ='staff desk by the east stairs, south of C ("there is a staff desk here & she is always here for all maps")'
OFF = [  # scan, sheet, area, posture, activity, gender, staff, count, where, note
    (1, 2, 'B', 'stand', '', 'M', 0, 1, 'between the shelves of B, on the north-south walkway', ''),
    (1, 2, 'B', 'sit_else', 'T', 'M', 0, 1, 'south-east of B, on the floor or ledge by the shelves', ''),
    (1, 2, 'C', 'sit_else', 'T', 'M', 0, 1, 'north-east of C, by the top of the east stairs', ''),
    (1, 2, 'D', 'stand', 'T', 'M', 0, 1, 'next to table D-25', ''),
    (1, 2, 'C', 'stand', 'T', 'F', 0, 1, 'between tables C-3 and C-15', ''),
    (1, 2, 'C', 'stand', 'T', 'M', 0, 1, 'east of table C-16', ''),
    (1, 2, 'C', 'stand', 'T', 'M', 0, 1, 'at the staff desk by the east stairs', ''),
    (1, 2, 'C', 'sit_other', 'O', 'F', 1, 1, STAFF_DESK, ''),
    (1, 2, 'D', 'walk', '', 'F', 0, 5, 'corridor south of D', '"5 girls" walking together'),
    (2, 2, 'D', 'stand', '', 'F', 0, 1, 'north of table D-3, with the presentation group', ''),
    (2, 2, 'D', 'stand', 'P', 'F', 0, 1, 'east edge of D, by the void', 'circled on the sheet'),
    (2, 2, 'D', 'stand', 'T', 'M', 0, 1, 'east edge of D, by the void', ''),
    (2, 2, 'D', 'stand', 'T', 'M', 0, 1, 'east edge of D, by the void', 'clarified: 2 males standing talking + 1 female on the phone walking around'),
    (2, 2, 'D', 'stand', 'T', 'M', 0, 1, 'corridor south of D, west of table D-25', ''),
    (2, 2, 'D', 'sit_other', 'T', 'M', 0, 1, 'chair in the corridor north of table D-25', ''),
    (2, 2, 'D', 'sit_else', 'P', 'F', 0, 1, 'single desk at the south-west corner of D', ''),
    (2, 2, 'C', 'stand', '', 'F', 0, 1, 'south of table C-11', '"She keeps walking around, leaves & comes back"'),
    (2, 2, 'C', 'stand', 'P', 'F', 0, 1, 'south-east of table C-11', ''),
    (2, 2, 'C', 'sit_other', 'O', 'F', 1, 1, STAFF_DESK, 'not drawn on this sheet; added from the observer\'s note'),
    (2, 2, 'C', 'walk', '', 'M', 0, 3, 'corridor south of C', '"group of 3" (clarified: 3 males)'),
    (3, 2, 'D', 'stand', 'T', 'F', 0, 1, 'east of table D-16', ''),
    (3, 2, 'D', 'stand', 'T', 'F', 0, 1, 'corridor south of D', ''),
    (3, 2, 'D', 'stand', '', 'F', 0, 1, 'corridor south of D', ''),
    (3, 2, 'D', 'stand', '', 'M', 0, 2, 'corridor south of D, north of table D-25', ''),
    (3, 2, 'C', 'stand', '', 'F', 0, 1, 'north of table C-3', ''),
    (3, 2, 'B', 'sit_else', 'T', 'M', 0, 3, 'south-east corner of B, on the floor or ledge',
     '"worker told them to not sit here & moved them at 1:50"'),
    (3, 2, 'C', 'sit_else', 'T', 'M', 0, 1, 'north-east of C, by the top of the east stairs', 'same group as above'),
    (3, 2, 'C', 'sit_other', 'O', 'F', 1, 1, STAFF_DESK, 'not drawn on this sheet; added from the observer\'s note'),
    (3, 2, 'D', 'walk', 'P', 'F', 0, 1, 'south of D', '"walking while talking on the phone"'),
    (3, 2, 'C', 'walk', '', 'M', 0, 5, 'towards the east stairs', '"5 people" leaving'),
    (3, 2, 'C', 'walk', '', 'F', 0, 5, 'towards the east stairs', '"5 people" leaving'),
    (3, 2, 'C', 'walk', '', 'F', 0, 3, 'towards the east stairs', '"3 people" leaving'),
    (3, 2, 'C', 'walk', '', 'M', 0, 7, 'corridor south of C, towards the east stairs', '"7 people" leaving'),
    (3, 2, 'D', 'walk', '', 'F', 0, 4, 'corridor south of D', '"4 people"'),
    (3, 2, 'C', 'walk', '', 'M', 0, 3, 'corridor between D and C', '"3 people"')]

OFF += [  # west ([researcher]); 'sit_else' between the shelves = on the floor
    (1, 1, 'A', 'stand', 'L', 'M', 1, 2, 'west bookshelves of A', '"two staff members arranging books"'),
    (1, 1, 'A', 'walk', '', 'F', 1, 1, 'north of A, through the access door', '"staff member went outside and then to toilet again"'),
    (1, 1, 'A', 'walk', '', 'M', 1, 1, 'all over the floor', '"staff member asking all over the library, someone has to fix a card"'),
    (1, 1, 'E', 'walk', '', 'F', 1, 1, 'between the handicapped toilet and the floor', '"staff member keeps going to the handicapped '
     'toilet and going back; she\'s moving all around the space"'),
    (1, 1, 'A', 'sit_other', 'O', 'M', 1, 2, 'information desk, south-east of A', '"staff members keep going back and forth, sitting/standing"'),
    (1, 1, 'A', 'stand', 'T', 'M', 1, 1, 'information desk, south-east of A', 'staff member standing'),
    (1, 1, 'A', 'stand', 'T', 'F', 0, 1, 'information desk, south-east of A', '"asking for something from staff"'),
    (1, 1, 'A', 'stand', '', 'M', 0, 1, 'north of table A-21', ''),
    (1, 1, 'A', 'stand', '', 'M', 0, 1, 'south of table A-21', ''),
    (1, 1, 'E', 'sit_other', '', 'M', 0, 3, 'south-west corner of E, chairs taken from other tables', '"group of boys took chairs from '
     'other tables and sat": new table arrangement'),
    # letters in these bubbles not reliable on this sheet -> all coded T (talking) as agreed, except the 2 who were studying
    (2, 1, 'A', 'sit_else', 'T', 'M', 0, 9, 'on the floor between the bookshelves of A and by the west wall', 'blue circles + 1 black '
     '(black = blue, male: observer); "new observation: between most bookshelves people were sitting on ground talking & playing, '
     'sleeping, eating (no one was studying except for 2)"; letters not reliable, coded T'),
    (2, 1, 'A', 'sit_else', 'T', 'F', 0, 8, 'on the floor between the bookshelves of A and by the west wall', 'red circles; coded T'),
    (2, 1, 'A', 'sit_else', 'S', 'F', 0, 2, 'on the floor between the bookshelves of A', '"two studying on ground": two females '
     'studying together in a group (red S; the arrow points to the A shelves, not the toilets)'),
    (2, 1, 'A', 'sit_else', 'O', 'F', 0, 1, 'north-west corner, on the floor', '"sleeping"'),
    (2, 1, 'A', 'stand', '', 'M', 0, 1, 'between the north bookshelves', ''),
    (2, 1, 'A', 'stand', '', 'M', 0, 2, 'by the main door', 'on the walking lines at the entrance'),
    (2, 1, 'A', 'stand', 'T', 'F', 0, 2, 'between tables A-3 and A-19', ''),
    (2, 1, 'A', 'stand', '', 'M', 0, 1, 'information desk, south-east of A', 'blue triangle (clarified)'),
    (2, 1, 'A', 'stand', 'T', 'F', 0, 1, 'information desk, south-east of A', '"asking something"'),
    (2, 1, 'E', 'stand', '', 'M', 0, 1, 'south of table E-23', ''),
    (2, 1, 'E', 'stand', '', 'F', 0, 1, 'east of table E-38', ''),
    (2, 1, 'A', 'walk', '', 'U', 0, 0, 'whole west half', '"there were a lot of people walking not marked here"'),
    # letters reliable on this sheet (observer) -> read from the colour photo
    (3, 1, 'A', 'sit_else', 'T', 'M', 0, 5, 'on the floor between the bookshelves of A and by the west wall', 'blue circles'),
    (3, 1, 'A', 'sit_else', 'P', 'M', 0, 1, 'on the floor between the bookshelves of A', 'blue circle'),
    (3, 1, 'A', 'sit_else', 'T', 'F', 0, 8, 'on the floor between the bookshelves of A and by the west wall', 'red circles, incl. a group '
     'of 5 by the toilets; "staff made all people on ground leave"; "staff member interrupted to tell people to get up"'),
    (3, 1, 'A', 'sit_else', 'P', 'F', 0, 2, 'on the floor between the north bookshelves of A', 'red circles'),
    (3, 1, 'A', 'sit_else', 'S', 'F', 0, 2, 'on the floor by the west wall of A', 'red circles'),
    (3, 1, 'A', 'sit_else', 'O', 'F', 0, 2, 'on the floor, north-west corner and west wall of A', '"sleeping on floor"'),
    (3, 1, 'A', 'stand', 'T', 'M', 0, 1, 'north of table A-5', ''),
    (3, 1, 'A', 'stand', '', 'F', 0, 2, 'north-east of A', ''),
    (3, 1, 'E', 'sit_else', 'O', 'F', 0, 1, 'south of E', '"sleeping" (clarified: female)')]

NOTES = [
    'EAST HALF ([researcher]). Main walking routes, all three scans: (1) the east-west corridor between the south row of D and area C, towards '
    'the east stairs - by far the busiest; (2) the north corridor along the group rooms, in front of the first rows of D and B; (3) a '
    'north-south walkway through B between tables B-3/4 and B-7/8, linking the north corridor with C and the stairs; (4) the walkway '
    'between D and B/C along the void.',
    'Scan 1 (10:00-10:35): "Big group mainly talking but studying too because they have laptops on" (D-1/2/7/8); "talking about work" '
    '(D-17 table); B-11 table "talking while working on laptop", written W, W = S; D-27/D-28 "came later"; one person left D-15 and '
    'someone came next to him; someone "went back again" into the north rooms; an empty extra chair at the south-west corner of D.',
    'Scan 2 (12:00-12:30): "They were a big group discussing a presentation they have; got up 12:15" (D-3 table); "walking around" in '
    'D; C-1 to C-12: "got up & people took their chairs", "they are talking about work", "eating & listening"; "she keeps walking around, '
    'leaves & comes back" (C); "2 people went to grab chairs and came back"; north of B: "this area could have inaccurate results as it '
    'is hidden & hard to observe" (about the walking lines there). Observer\'s general note: some '
    'arrows stand for a group instead of one person each, for ease of drawing.',
    'Scan 3 (13:30-14:00): "at 1:45 changed people & new people have an architecture drawing" and "moving chair" (D void); "left & put '
    'their chairs back" (D-3 table); four people sitting on the floor by the shelves at the south-east of B: "worker told them to not sit '
    'here & moved them at 1:50"; "around 1:55 people started leaving in big groups - for both east & west maps"; "Generally the same '
    'people use the library, we see a lot of familiar faces". A separate "seating only at 2:00" sheet records the seats after people '
    'started leaving (not used as a scan).',
    'Pen colours 24 Nov: black = male, red = female, blue = cannot tell (key corrected on sheet scan 3: "check this for all maps").',
    'WEST HALF ([researcher]), from her colour photos. Key as printed: blue = male, red = female, black = cannot tell. Note for all scans: an '
    'access door that is not drawn on the plan, at the north-west of area A (close-up on the last page of her scan); staff and students '
    'use it, and many walking lines start or end there. Main routes: from the main door at the north-east of A south along the east '
    'edge of A and E (the busiest west route), the east-west link between A and E towards the toilets, and loops around the tables of A '
    'and E by students looking for a seat.',
    'West scan 1 (10:00-10:35): staff very present - two staff members arranging books, one "asking all over the library, someone has '
    'to fix a card", one "keeps going to the handicapped toilet and going back", staff "keep going back and forth, sitting/standing" at '
    'the information desk; "girl grabbed a chair from another table, talking on the phone" (A-23/A-31); "girl sat on her phone then '
    'left" (A-25); "new people came"; "group of boys took chairs from other tables and sat" (new table arrangement, south-west of E); '
    '"girl keeps moving around the table" (E-35); "dropped belongings, went to toilet & back"; "looked for a chair & went back"; "went '
    'to table, moved a chair to another table".',
    'West scan 2 (12:00-12:30): "new observation: between most bookshelves, in those spots people were sitting on the ground talking & '
    'playing, sleeping, eating (no one was studying except for 2)"; "note: didn\'t mark the letters inside the bubbles correctly in '
    'this part"; "there were a lot of people walking not marked here"; "two studying on ground" (by the toilets); "guy came and sat '
    'studying" (E-3); E-21 table "studying together", later "they were all talking"; people exiting the library.',
    'West scan 3 (13:30-14:00): "all talking together" (A-1 table); about 19 people on the floor between the shelves, including '
    '"sleeping on floor" and "talking on the phone"; "staff member interrupted to tell people to get up" and "staff made all people on '
    'ground leave"; "all these people left" (A tables, about 13:55, matching [researcher]\'s note); "2 people left the table" (E-17); a person '
    '"sleeping" south of E. Note "some of them left and repeated - mirror it on x & y axis so the corner goes to its exact opposite '
    'corner" (meaning to confirm with the observer). A separate "seating only at 2 pm" sheet exists, as for the east half.',
    'East-west consistency: both halves record people leaving in big groups at about 13:55; staff are far more visible in the west half '
    '(information desk, book arranging); sitting on the floor between the shelves is recorded mainly in the west half (scans 2 and 3) and '
    'at the south-east of B (scan 3), where a worker also moved people at 13:50.',
    'Clarifications from the observers (24 Nov 2026, evening): every unclear gender and letter was answered (no "cannot tell" left). '
    '[researcher]: black marks on her sheets are blue = male; "ex" alone in a circle = an empty extra chair; any note saying a person is '
    'sleeping = O; on sheet scan 4 the letters of the people sitting on the floor are not reliable and are coded T, except the two '
    'studying together (S); on sheet scan 5 they are reliable. On sheet scan 5 the seats inside the box round the A tables were drawn '
    'mirrored on both axes and have been flipped (A-n -> A-33-n); the extra chairs, lines and notes there are correct as drawn. '
    '[researcher]: his corrected pen key (black = male, red = female) applies to his sheet scans 3-5 only (24 Nov); 19 Nov keeps its own key. '
    'The note "this area could have inaccurate results as it is hidden & hard to observe" (north of B) is about the walking lines there, '
    'not the tables: few people walk there because there are only tables below the group rooms. '
    'Staff (information desk, staff desk, book arranging, staff walking) are kept in these files but left out of all people counts. '
    'The "seating only at 2:00" sheets are kept as notes on who got up after 13:55, not as a scan.']

seats = L.build()
rows = []
for scan, sheets in SCANS.items():
    occ = {}
    for code, (m, g) in MARKS[scan].items():
        if m in ('S', 'T', 'P', 'O', 'L', 'U'): occ.setdefault(seats.set_index('code').loc[code, 'table'], []).append(code)
    gid = {c: f'G{scan}.{k}' for k, cs in enumerate(sorted(occ.values())) if len(cs) > 1 for c in cs}   # same table = one group
    for r in seats.itertuples():
        sh = SHEET_OF(r.code)
        if sh not in SIDES_DONE: continue
        start, end, obs = sheets[sh]
        m, g = MARKS[scan].get(r.code, ('', ''))
        rows.append(dict(date=DATE, scan=scan, sheet=sh, start=start, end=end, observer=obs, seat=r.code, zone=r.zone, mark=m,
                         occupied=int(m in ('S', 'T', 'P', 'O', 'L', 'U')), gender=g, group=gid.get(r.code, ''),
                         unsure=UNSURE.get((scan, r.code), '')))
out = pd.DataFrame(rows)
bad = [k for s in MARKS for k in MARKS[s] if k not in set(seats.code)]
assert not bad, bad
assert set(out[out.occupied == 1].gender) <= {'M', 'F', 'U'}, 'occupied seat without a gender'
out.to_csv(os.path.join(HERE, f'behaviour_mapping_{DATE}.csv'), index=False)
pd.DataFrame(EXTRAS, columns=['scan', 'table_first_seat', 'count', 'activity', 'gender', 'note']).to_csv(
    os.path.join(HERE, f'behaviour_mapping_{DATE}_extras.csv'), index=False)
pd.DataFrame(OFF, columns=['scan', 'sheet', 'area', 'posture', 'activity', 'gender', 'staff', 'count', 'where', 'note']).to_csv(
    os.path.join(HERE, f'behaviour_mapping_{DATE}_people_off_seats.csv'), index=False)
open(os.path.join(HERE, f'behaviour_mapping_{DATE}_notes.txt'), 'w', encoding='utf-8').write('\n\n'.join(NOTES))
for s in SCANS:
    q = out[out.scan == s]; e = [x for x in EXTRAS if x[0] == s and x[3]]; o = [x for x in OFF if x[0] == s]
    print(f'scan {s} (sheet {SHEET_SCAN_NO[s]}):', q[q.mark != ''].mark.value_counts().to_dict(),
          f'| on seats {int(q.occupied.sum())}, extras {sum(x[2] for x in e)}, off seats {sum(x[7] for x in o)}',
          '| unsure', int((q.unsure != '').sum()))
