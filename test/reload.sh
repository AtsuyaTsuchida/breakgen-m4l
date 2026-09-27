#!/bin/bash
# Rebuild, replace the BreakGen track in Live and reload the device.
cd "$(dirname "$0")/.." && python3 build.py >/dev/null
IDX=$(python3 test/live.py get_session_info | python3 -c "import json,sys;print(json.load(sys.stdin)['result']['track_count'])")
for ((i=0;i<IDX;i++)); do
  N=$(python3 test/live.py get_track_info "{\"track_index\":$i}" | python3 -c "import json,sys;print(json.load(sys.stdin)['result']['name'])")
  if [ "$N" = "BreakGen" ]; then python3 test/live.py delete_track "{\"track_index\":$i}" >/dev/null; break; fi
done
T=$(python3 test/live.py create_midi_track '{"index":-1}' | python3 -c "import json,sys;print(json.load(sys.stdin)['result']['index'])")
python3 test/live.py set_track_name "{\"track_index\":$T,\"name\":\"BreakGen\"}" >/dev/null
python3 test/live.py load_user_sample "{\"track_index\":$T,\"path\":\"Presets/Instruments/Max Instrument/BreakGen/BreakGen\"}"
echo "track=$T"
