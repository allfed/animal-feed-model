# Changes

- Moved to a single csv with sources
- Removed hard-code of poultry numbers, they are now in the CSV also.
- Feed numbers are still hardcoded for now
- Refined some numbers and small bugs/inaccuracies in the input data
- Changed to head (removed magnitude adjust, 1000 head references in the code)
- Moved input sliders to a class, now can be pre-defined from CSV or other method OR use the dash sliders
- These changes seem to hav broken Heroku, but it still works on local host (or heroku is having unrelated downtime problems... but seems unlikely)
- I've maintained the usage of residues, but I'm unsure of the effect (haven't looked too closely yet)