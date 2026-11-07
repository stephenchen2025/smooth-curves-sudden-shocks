#!/usr/bin/env bash
# Collect the attention series and run A2-A4 end to end. Needs open internet; about 30-60 minutes,
# mostly Google Trends back-off. Re-running skips series that were already collected.
set -uo pipefail
cd "$(dirname "$0")"
python -m pip install -q -r requirements.txt

collect () {  # collect <cmd> <file>
  if [ -s "$2" ]; then echo "have $2"; return 0; fi
  echo "collecting $2 ..."
  python attention.py "$1" --out "$2" || { echo "!! $1 failed; continuing without it"; rm -f "$2"; }
}
collect wikipedia data/wiki.csv
collect gdelt-doc data/gdelt.csv
collect trends    data/trends.csv

[ -s data/wiki.csv ] && python scripts/compare_wiki.py data/wiki.csv data/wiki_hf.csv

inputs=()
for f in data/wiki.csv data/trends.csv data/gdelt.csv; do [ -s "$f" ] && inputs+=("$f"); done
if [ ${#inputs[@]} -eq 0 ]; then echo "no attention series collected"; exit 1; fi
echo "running the analysis on: ${inputs[*]}"
python scripts/run_attention.py --inputs "${inputs[@]}" --out out/attention_full
echo "done: results in out/attention_full/summary.json (send that folder back)"
