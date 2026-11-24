# Walking routes from the behavioural maps: method note (24 Nov 2026)

Source: van Nes, A., & Yamu, C. (2021). Empirical data collection and analysis, and connecting data with space syntax. In
*Introduction to Space Syntax in Urban Studies* (pp. 133-170). Springer. https://doi.org/10.1007/978-3-030-59140-3_5
(open access, CC BY) - PDF: `sources/methods/vanNes_Yamu_2021_Ch5_EmpiricalDataCollection.pdf`.

## What the source says (page numbers of the book)
- **General movement traces (5.2.4, p. 144):** from a fixed position with a wide view, the observer draws every movement
  trace, in all directions, on a printed map for a set time, repeated several times through the day. This is what our
  observers did: each scan, every person walking was drawn as a line with an arrow on the sheet.
- **Gate counts (5.2.1, pp. 135-137):** an imaginary line across a route; only people who cross it are counted, tallied by
  category (the book lists men and women among the usual categories, p. 137), and the start and end times are noted so
  counts can be turned into rates. Repeat over several time slots and days.
- **Static snapshots (5.2.2, pp. 138-141):** what people are doing at one moment, repeated through the day, and split by
  gender in the example maps (Fig. 5.7). This matches the seat part of our maps.

## What we did
Count lines ("gates") were placed afterwards on the drawn traces, in the same sheet position on every sheet: 5 in the east
half, 5 in the west half (`data/route_gates.py`). Every trace crossing a gate was counted by eye, by pen colour (apparent
gender); a trace labelled as a group counts as that many people; staff traces are left out. Direction = the arrowheads
([researcher] drew one arrow per line on his 24 Nov sheets, so every arrowhead along a corridor was counted there). Counts are in
`data/route_counts.csv`, the map in `results/figures/route_density.png`.

## Differences from the book (for the limitations)
- Traces were drawn over a 30-35 min scan, not 5-min periods, so a busy corridor could not be fully drawn ([researcher], scan 4:
  "there were a lot of people walking not marked here"); counts are density markers (about +/- 2 lines per gate).
- 10 gates over 2 days (5 scans); the book suggests at least 25 gates per area and more days, including weekends.
- Gates were placed on the drawings afterwards, not counted live on site.
- Pen keys: [researcher]'s 19 Nov lines blue = female, black = male (he swapped them for lines only); his 24 Nov sheets black =
  male, red = female. [researcher]'s lines follow her circles (19 Nov blue = male, black = female; 24 Nov blue = male, red = female).
