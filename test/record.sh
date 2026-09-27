#!/bin/bash
# Record BreakGen output for N seconds into test/live_render.wav
cd "$(dirname "$0")/.."
SECS=${1:-12}
REC=$(python3 -c 'import sys;sys.path.insert(0,"test");from bg import track;print(track("BG_Rec"))')
python3 test/live.py set_track_routing "{\"track_index\":$REC,\"input_routing\":\"Resampling\",\"monitoring\":2,\"arm\":1}" >/dev/null
# move the selection off BreakGen so auto-arm doesn't record over its MIDI clip
python3 test/live.py load_user_sample "{\"track_index\":$REC,\"path\":\"Samples/BreakGen/cw_amen01_175.wav\"}" >/dev/null
BG=$(python3 -c 'import sys;sys.path.insert(0,"test");from bg import track;print(track())')
python3 test/live.py set_track_routing "{\"track_index\":$BG,\"arm\":0}" >/dev/null
touch "$TMPDIR/recmark"
python3 test/live.py set_song_props '{"loop":false,"current_song_time":0,"record_mode":true}' >/dev/null
python3 test/live.py start_playback >/dev/null; sleep "$SECS"; python3 test/live.py stop_playback >/dev/null
python3 test/live.py set_song_props '{"record_mode":false}' >/dev/null
python3 test/live.py set_track_routing "{\"track_index\":$REC,\"arm\":0}" >/dev/null
sleep 1
F=$(find ~/Music/Ableton/Live\ Recordings -newer "$TMPDIR/recmark" -name "BG_Rec*.wav" | head -1)
cp "$F" test/live_render.wav && echo "recorded: $F"
