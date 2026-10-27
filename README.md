# SJQP — Residential Site Planning Prototype

Python configurable concept massing engine. Generates candidates across rows, staggered rows, mixed heights, and towers; ranks by capacity, relative value, and comfort proxy.

> **Not compliant design certification.** Daylight, fire access, parking, road layout and local statutory requirements are NOT validated. Example parcel is synthetic. This repository must not receive confidential site datasets while public.

## Quick start

```sh
pip install -r requirements.txt
python -m unittest discover -s tests -v
python engine.py example_site.json --iterations 80 --output results.json
python tests/report.py results.json > validation_report.md
```

Workflow `.github/workflows/validate.yml` runs weekly, on pushes and manually, and uploads results as artifacts. No automatic algorithm code modifications or automatic merges. Official-case reverse calibration remains future work; NEVER weaken a superior valid model result to match an observed plan.
