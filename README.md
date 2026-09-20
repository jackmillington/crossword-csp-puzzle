# Crossword Constraint Satisfaction Solver

A Python crossword generator that models word placement as a constraint satisfaction problem (CSP).

The solver reduces candidate domains using node and arc consistency, then completes the puzzle with backtracking search and variable/value ordering heuristics.

## Techniques implemented

- node consistency
- AC-3 arc consistency
- backtracking search
- minimum remaining values (MRV)
- degree heuristic
- least-constraining-value ordering
- overlap consistency checks
- all-different word constraints

## How it works

Each crossword slot is represented as a variable with:

- row and column position
- direction
- required word length
- overlapping variables

Candidate words form the domain for each variable. The solver first removes impossible values, propagates overlap constraints, then searches for a complete consistent assignment.

## Run

From the `crossword/` directory:

```bash
python generate.py data/structure0.txt data/words0.txt
```

To save the completed crossword as an image:

```bash
python generate.py data/structure0.txt data/words0.txt output.png
```

Alternative structures and word lists are included under `data/`.

## Main files

| File | Purpose |
| --- | --- |
| `crossword/crossword.py` | Parses the grid and builds variables, domains and overlap relationships |
| `crossword/generate.py` | Constraint propagation, search and rendering |
| `crossword/data/` | Example crossword structures and vocabularies |

## Stack

- Python
- constraint satisfaction
- AC-3
- backtracking search
- Pillow
