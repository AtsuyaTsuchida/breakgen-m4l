# BreakGen (Max for Live)

A sampling breakbeat generator that runs entirely inside Max: it fetches a break, slices and
analyses it, plays the slices with its own poly~ sampler, and writes a MIDI clip to the
arrangement.

- Device: `~/Music/Ableton/User Library/Presets/Instruments/Max Instrument/BreakGen/BreakGen.amxd`
- Downloads and CREDITS.txt: `~/Music/Ableton/User Library/Samples/BreakGen/`

## Usage
1. Drop BreakGen onto an empty MIDI track (put it directly on the track, not inside a rack).
2. Load a sample:
   - **Amen (classic)**: choose 1–20 with Pick, then press Fetch (archive.org `amen-breaks`; clear the rights before releasing).
   - **Freesound CC**: enter an API key in the right-hand text field and press Return, type a search term (e.g. `drum break`) in the middle field and press Return, then Fetch. Only CC0 and CC BY sounds are fetched (preview mp3), and credits are appended to CREDITS.txt.
   - **URL**: type an http(s) URL to a wav, mp3 or aiff file in the middle field, then Fetch.
   - **Local file**: drag it onto the Drop area.
3. Choose Style (Jungle/DnB, Juke/Footwork, Boom Bap, Breaks/UKG). Changing it resets the eight dials to that style's defaults.
4. Set Bars, Bar (start bar) or @Playhead, and Seed (0 means random), then press **Generate**. The clip is written into the arrangement.
5. **Set Tempo** switches Live's tempo to the style's typical BPM. **Sync** repitches the sample to follow the song tempo.

| Dial | Effect |
|---|---|
| Density | Amount of hats and filler hits |
| Chop | How much beat-sized chunks of the original are rearranged |
| Ghost | Amount of ghost snares |
| Roll | Frequency of snare/kick rolls (32nds, 16th triplets) |
| Reverse | Frequency of reversed slices |
| Swing | Delay applied to 16th offbeats (100 = triplet) |
| Fill | Chance of a fill at the end of each 4-bar phrase |
| Strength | How strictly the style's kick/snare skeleton is enforced |

The MIDI notes C1 (36) through B4 map to slices 1–48. C5 (84) and above play the same slices reversed. Pitch, Length (slice length) and Choke (a new hit cuts the previous one) change how the slices play back.

## Installation
Copy `build/BreakGen.amxd`, `build/bg_voice.maxpat` and `build/breakgen.js` into one folder in your Ableton User Library (for example `Presets/Instruments/Max Instrument/BreakGen/`), or run `python3 build.py`, which builds and installs them there. Requires Live 12 Suite (or Live 12 with Max for Live, which bundles Max 9).

## Development
- `breakgen.js`: analysis (spectral-flux onsets, BPM and loop-length fit, K/S/G/H classification), pattern generation, and the Live API glue.
- `build.py`: generates `BreakGen.amxd` and `bg_voice.maxpat` and installs them into the User Library (`python3 build.py`).
- Analysis and classification accuracy (`python3 test/evaluate.py data/test`) is measured on labelled breaks synthesised from Live's Core Library one-shots (`test/synth_dataset.py`; train and test use different sounds):
  - Onset detection: band-wise SuperFlux, then the steepest rise of a 1.5 ms envelope
  - BPM: each whole-number loop length is scored by 16th-grid fit, backbeat, kick on the one, a tempo prior, and a penalty for non-power-of-two beat counts
  - Classification: two MLP stages (spectral features, then metrical position and neighbouring slices), trained with `test/train.py` and `test/crossfit.sh` and embedded into breakgen.js by `test/inject_model.py`
  - Test-set results: BPM 95%, onset recall 87% / precision 90%, K/S/G/H accuracy 92%
- `test/run_test.js`: tests analysis and generation outside Max with the macOS JavaScriptCore `jsc`. Audio is not included in the repository; download test loops yourself, for example `curl -L -o test/cw_amen01_175.wav https://archive.org/download/amen-breaks/cw_amen01_175.wav`.
- `test/render.py`: renders generated patterns offline to WAV.
- `test/reload.sh` / `bg.py` / `record.sh`: reload the device, drive its parameters, and record its output in Live through AbletonMCP (port 9877).
- Debugging: set `DEBUG_URL` in `breakgen.js` and run `python3 test/logserver.py test/device.log` to receive the log. The log is also written to `breakgen.log` in the device folder.
