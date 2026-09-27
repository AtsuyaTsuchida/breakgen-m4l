#!/usr/bin/env python3
"""Build BreakGen.amxd (Max for Live instrument) + bg_voice.maxpat and install them
into the Ableton User Library next to breakgen.js."""
import json, os, shutil, struct

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL = os.path.expanduser("~/Music/Ableton/User Library/Presets/Instruments/Max Instrument/BreakGen")
DOWNLOADS = os.path.expanduser("~/Music/Ableton/User Library/Samples/BreakGen")


class Patch:
    def __init__(self):
        self.boxes, self.lines, self.n = [], [], 0

    def box(self, maxclass="newobj", txt=None, ins=1, outs=0, outtype=None, rect=(0, 0, 80, 22),
            pres=None, **kw):
        self.n += 1
        bid = "obj-%d" % self.n
        b = {"id": bid, "maxclass": maxclass, "numinlets": ins, "numoutlets": outs,
             "patching_rect": list(rect)}
        if outs:
            b["outlettype"] = outtype or [""] * outs
        if txt is not None:
            b["text"] = txt
        if pres:
            b["presentation"] = 1
            b["presentation_rect"] = list(pres)
        b.update(kw)
        self.boxes.append({"box": b})
        return bid

    def obj(self, text, ins, outs, x, y, w=None, outtype=None, **kw):
        return self.box("newobj", text, ins, outs, outtype, (x, y, w or max(40, 7 * len(text)), 22), **kw)

    def msg(self, text, x, y, w=None):
        return self.box("message", text, 2, 1, [""], (x, y, w or max(30, 7 * len(text)), 22))

    def wire(self, a, ao, b, bi):
        self.lines.append({"patchline": {"source": [a, ao], "destination": [b, bi]}})

    def patcher(self, **extra):
        p = {"fileversion": 1,
             "appversion": {"major": 9, "minor": 1, "revision": 5, "architecture": "x64", "modernui": 1},
             "classnamespace": "box", "rect": [80, 80, 1300, 800], "bglocked": 0,
             "openinpresentation": 0, "default_fontsize": 10.0, "default_fontface": 0,
             "default_fontname": "Arial Bold", "gridonopen": 1, "gridsize": [8.0, 8.0],
             "gridsnaponopen": 1, "objectsnaponopen": 1, "statusbarvisible": 2, "toolbarvisible": 1,
             "boxes": self.boxes, "lines": self.lines}
        p.update(extra)
        return {"patcher": p}


def param(longname, ptype, mmin=None, mmax=None, initial=None, unit=None, enum=None, shortname=None):
    v = {"parameter_longname": longname, "parameter_shortname": shortname or longname,
         "parameter_type": ptype}
    if mmin is not None:
        v["parameter_mmin"] = mmin
    if mmax is not None:
        v["parameter_mmax"] = mmax
    if initial is not None:
        v["parameter_initial"] = [initial]
        v["parameter_initial_enable"] = 1
    if unit is not None:
        v["parameter_unitstyle"] = unit
    if enum is not None:
        v["parameter_enum"] = enum
    return {"saved_attribute_attributes": {"valueof": v}, "varname": longname}


# ---------------------------------------------------------------------------
# Voice (inside poly~). Receives "p v" (note), setbuf/pitch/len/mono/stop.
def build_voice():
    P = Patch()
    o = P.obj
    inl = o("in 1", 0, 1, 20, 20)
    rt = o("route note setbuf pitch len mono stop", 1, 7, 20, 60, 260)
    P.wire(inl, 0, rt, 0)
    up = o("unpack i i", 1, 2, 20, 100)
    P.wire(rt, 0, up, 0)
    P.wire(rt, 6, up, 0)   # unmatched -> plain "p v" list
    gain = o("expr pow($f1/127.\\, 1.5)", 1, 1, 200, 140, 150)
    P.wire(up, 1, gain, 0)
    t3 = o("t i i", 1, 2, 20, 140)
    P.wire(up, 0, t3, 0)
    rev = o("expr $i1>=84", 1, 1, 90, 180)
    P.wire(t3, 1, rev, 0)
    idx = o("expr $i1-36-48*($i1>=84)", 1, 1, 20, 220, 160)
    P.wire(t3, 0, idx, 0)
    t2 = o("t i i", 1, 2, 20, 260)
    P.wire(idx, 0, t2, 0)
    pk_end = o("peek~ bgv_none 2", 3, 1, 110, 300)
    pk_st = o("peek~ bgv_none 1", 3, 1, 20, 300)
    P.wire(t2, 1, pk_end, 0)
    P.wire(t2, 0, pk_st, 0)
    tS = o("t f f", 1, 2, 20, 340)
    P.wire(pk_st, 0, tS, 0)
    lenx = o("expr ($f2-$f1)*$f3", 3, 1, 20, 380, 130)
    P.wire(tS, 0, lenx, 0)
    P.wire(pk_end, 0, lenx, 1)
    t_len = o("t f f f", 1, 3, 20, 420)
    P.wire(lenx, 0, t_len, 0)
    durx = o("expr $f1/$f2", 2, 1, 260, 460)
    ex = o("expr $f2+$f1*(1-$f3)", 3, 1, 140, 460, 120)
    sx = o("expr $f2+$f1*$f3", 3, 1, 20, 460, 110)
    P.wire(t_len, 2, durx, 0)
    P.wire(t_len, 1, ex, 0)
    P.wire(t_len, 0, sx, 0)
    for x in (ex, sx):
        P.wire(tS, 1, x, 1)
        P.wire(rev, 0, x, 2)
    pk = o("pack f f f", 3, 1, 20, 500)
    P.wire(sx, 0, pk, 0)
    P.wire(ex, 0, pk, 1)
    P.wire(durx, 0, pk, 2)
    tr = o("t b l l", 1, 3, 20, 540)
    P.wire(pk, 0, tr, 0)
    pst = o("prepend start", 1, 1, 300, 580)
    P.wire(tr, 2, pst, 0)
    ul = o("unpack f f f", 1, 3, 160, 580)
    P.wire(tr, 1, ul, 0)
    hold = o("expr max($f1-6.\\, 0.)", 1, 1, 160, 620, 130)
    P.wire(ul, 2, hold, 0)
    envm = P.msg("0, 1 2 1 $1 0 4", 160, 660, 110)
    P.wire(hold, 0, envm, 0)
    busy1 = P.msg("1", 20, 660)
    P.wire(tr, 0, busy1, 0)
    stopm = P.msg("0 4", 300, 660)
    P.wire(rt, 5, stopm, 0)
    line = o("line~", 2, 2, 160, 700, outtype=["signal", "bang"])
    P.wire(envm, 0, line, 0)
    P.wire(stopm, 0, line, 0)
    busy0 = P.msg("0", 240, 740)
    P.wire(line, 1, busy0, 0)
    tp = o("thispoly~", 1, 2, 20, 780)
    P.wire(busy1, 0, tp, 0)
    P.wire(busy0, 0, tp, 0)
    m = o("*~ 0.", 2, 1, 160, 740, outtype=["signal"])
    P.wire(line, 0, m, 0)
    P.wire(gain, 0, m, 1)
    # params
    pitchx = o("expr pow(2.\\, $f1/12.)", 1, 1, 420, 100, 140)
    P.wire(rt, 2, pitchx, 0)
    P.wire(pitchx, 0, durx, 1)
    P.wire(rt, 3, lenx, 2)
    monox = o("!- 2", 2, 1, 420, 140)
    P.wire(rt, 4, monox, 0)
    # buffers
    ub = o("unpack s s", 1, 2, 580, 100)
    P.wire(rt, 1, ub, 0)
    setp = o("prepend set", 1, 1, 580, 140)
    sets = o("prepend set", 1, 1, 680, 140)
    P.wire(ub, 0, setp, 0)
    P.wire(ub, 1, sets, 0)
    P.wire(sets, 0, pk_st, 0)
    P.wire(sets, 0, pk_end, 0)
    play = o("play~ bgv_none 2", 2, 3, 300, 620, outtype=["signal", "signal", "bang"])
    P.wire(setp, 0, play, 0)
    P.wire(pst, 0, play, 0)
    sel = o("selector~ 2 2", 3, 1, 400, 700, outtype=["signal"])
    P.wire(monox, 0, sel, 0)
    P.wire(play, 0, sel, 1)
    P.wire(play, 1, sel, 2)
    mL = o("*~", 2, 1, 300, 780, outtype=["signal"])
    mR = o("*~", 2, 1, 400, 780, outtype=["signal"])
    P.wire(play, 0, mL, 0)
    P.wire(sel, 0, mR, 0)
    P.wire(m, 0, mL, 1)
    P.wire(m, 0, mR, 1)
    oL = o("out~ 1", 1, 0, 300, 820)
    oR = o("out~ 2", 1, 0, 400, 820)
    P.wire(mL, 0, oL, 0)
    P.wire(mR, 0, oR, 0)
    # defaults
    lb = o("loadbang", 1, 1, 420, 20)
    d0 = P.msg("0", 420, 60)
    d1 = P.msg("1.", 470, 60)
    P.wire(lb, 0, d0, 0)
    P.wire(lb, 0, d1, 0)
    P.wire(d0, 0, pitchx, 0)
    P.wire(d0, 0, monox, 0)
    P.wire(d1, 0, lenx, 2)
    return P.patcher()


# ---------------------------------------------------------------------------
# Device
def build_device():
    P = Patch()
    o = P.obj
    v8 = o("v8 breakgen.js", 1, 8, 600, 420, 300)

    # MIDI -> voices
    mi = o("midiin", 1, 1, 20, 20)
    mp = o("midiparse", 1, 8, 20, 50)
    P.wire(mi, 0, mp, 0)
    up = o("unpack i i", 1, 2, 20, 80)
    P.wire(mp, 0, up, 0)
    sn = o("stripnote", 2, 2, 20, 110)
    P.wire(up, 0, sn, 0)
    P.wire(up, 1, sn, 1)
    pk = o("pack i i", 2, 1, 20, 140)
    P.wire(sn, 1, pk, 1)
    P.wire(sn, 0, pk, 0)
    tt = o("t l b", 1, 2, 20, 170)
    P.wire(pk, 0, tt, 0)
    gate = o("gate 1 1", 2, 1, 120, 200)
    P.wire(tt, 1, gate, 1)
    stopm = P.msg("stop", 120, 230)
    P.wire(gate, 0, stopm, 0)
    pn = o("prepend note", 1, 1, 20, 230)
    P.wire(tt, 0, pn, 0)
    poly = o("poly~ bg_voice 16 @steal 1", 1, 2, 20, 280, 200, outtype=["signal", "signal"])
    P.wire(pn, 0, poly, 0)
    P.wire(stopm, 0, poly, 0)
    P.wire(v8, 0, poly, 0)
    P.wire(v8, 4, gate, 0)
    gain = P.box("live.gain~", None, 2, 5, ["signal", "signal", "", "float", "list"], (20, 320, 48, 136),
                 pres=(872, 4, 40, 160), orientation=1, showname=0, shownumber=1,
                 **param("Volume", 0, -70.0, 6.0, 0.0, 4))
    P.wire(poly, 0, gain, 0)
    P.wire(poly, 1, gain, 1)
    # level meter for diagnostics (v8 only logs it when DEBUG_URL is set)
    pa = o("peakamp~ 250", 2, 1, 120, 320)
    P.wire(poly, 0, pa, 0)
    pl = o("prepend lvl", 1, 1, 120, 350)
    P.wire(pa, 0, pl, 0)
    P.wire(pl, 0, v8, 0)
    po = o("plugout~", 2, 0, 20, 470)
    P.wire(gain, 0, po, 0)
    P.wire(gain, 1, po, 1)

    # buffers
    brk = o("buffer~ ---bg_break", 1, 2, 300, 520, 140, outtype=["float", "bang"])
    slb = o("buffer~ ---bg_slices 50 2", 1, 2, 460, 520, 160, outtype=["float", "bang"])
    P.wire(v8, 1, brk, 0)
    loadedm = P.msg("loaded", 300, 560)
    P.wire(brk, 1, loadedm, 0)
    P.wire(loadedm, 0, v8, 0)

    # init
    td = o("live.thisdevice", 1, 3, 300, 20, 100)
    tb = o("t b b b", 1, 3, 300, 50)
    P.wire(td, 0, tb, 0)
    setbuf = P.msg("target 0, setbuf ---bg_break ---bg_slices", 300, 90, 260)
    P.wire(tb, 2, setbuf, 0)
    P.wire(setbuf, 0, poly, 0)
    wset = P.msg("set ---bg_break", 580, 90, 110)
    P.wire(tb, 1, wset, 0)
    initm = P.msg("names ---bg_break ---bg_slices, init", 300, 130, 230)
    P.wire(tb, 0, initm, 0)
    P.wire(initm, 0, v8, 0)

    # maxurl
    mu = o("maxurl", 1, 2, 900, 520, outtype=["dictionary", "list"])
    P.wire(v8, 2, mu, 0)
    P.wire(mu, 0, v8, 0)

    # state
    pat = P.box("newobj", "pattr bgstate", 1, 3, ["", "", ""], (1000, 470, 90, 22),
                **param("BreakGenState", 3))
    P.boxes[-1]["box"]["saved_attribute_attributes"]["valueof"]["parameter_invisible"] = 1
    P.boxes[-1]["box"]["parameter_enable"] = 1
    P.wire(v8, 7, pat, 0)
    pr = o("prepend restore", 1, 1, 1000, 500)
    P.wire(pat, 0, pr, 0)
    P.wire(pr, 0, v8, 0)

    # ---- UI (presentation)
    def to_v8(src, name, outlet=0, x=None, y=None):
        pp = o("prepend " + name, 1, 1, x if x is not None else 600, y if y is not None else 380)
        P.wire(src, outlet, pp, 0)
        P.wire(pp, 0, v8, 0)
        return pp

    ux = 20  # patching x cursor for UI objects
    def nx(w=70):
        nonlocal ux
        ux += w + 10
        return ux

    # source row
    src = P.box("live.menu", None, 1, 3, ["", "", "float"], (nx(), 700, 80, 15), pres=(4, 4, 86, 15),
                **param("Source", 2, 0, 2, 0, None, ["Amen (classic)", "Freesound CC", "URL"]))
    to_v8(src, "source", x=ux, y=740)
    pick = P.box("live.numbox", None, 1, 2, ["", "float"], (nx(), 700, 40, 15), pres=(94, 4, 36, 15),
                 **param("Pick", 1, 1, 99, 1, 0))
    to_v8(pick, "pick", x=ux, y=740)
    fetchb = P.box("live.text", None, 1, 2, ["", ""], (nx(), 700, 44, 15), pres=(134, 4, 44, 15), mode=0,
                   text="Fetch", **param("Fetch", 2, 0, 1, None, None, ["off", "on"]))
    to_v8(fetchb, "fetchsrc", x=ux, y=740)
    q = P.box("textedit", None, 1, 4, ["", "int", "", ""], (nx(), 700, 180, 18), pres=(182, 3, 180, 18),
              text="drum break", lines=1, keymode=1, fontsize=10.0)
    to_v8(q, "query", x=ux, y=740)
    kt = P.box("textedit", None, 1, 4, ["", "int", "", ""], (nx(180), 700, 100, 18), pres=(366, 3, 100, 18),
               text="", lines=1, keymode=1, fontsize=10.0, hint="Freesound API key")
    to_v8(kt, "key", x=ux, y=740)
    rtxt = o("route query key", 1, 3, 1100, 470)
    P.wire(v8, 6, rtxt, 0)
    P.wire(rtxt, 0, q, 0)
    P.wire(rtxt, 1, kt, 0)

    wf = P.box("waveform~", None, 5, 6, ["float", "float", "float", "float", "list", ""], (nx(100), 700, 360, 70),
               pres=(4, 24, 360, 72), buffername="---bg_break", setmode=0, grid=0)
    P.wire(wset, 0, wf, 0)
    P.wire(brk, 1, wset, 0)
    dropb = P.box("live.drop", None, 1, 2, ["", ""], (nx(360), 700, 98, 72), pres=(368, 24, 98, 72))
    to_v8(dropb, "drop", x=ux, y=780)
    stat = P.box("comment", None, 1, 0, None, (20, 620, 460, 18), pres=(4, 100, 462, 30),
                 text="BreakGen", linecount=2, fontsize=9.5, textcolor=[0.85, 0.85, 0.85, 1.0])
    P.wire(v8, 3, stat, 0)

    # right block
    sty = P.box("live.menu", None, 1, 3, ["", "", "float"], (nx(100), 700, 90, 15), pres=(474, 4, 92, 15),
                **param("Style", 2, 0, 3, 0, None, ["Jungle/DnB", "Juke/Footwork", "Boom Bap", "Breaks/UKG"]))
    to_v8(sty, "style", x=ux, y=740)
    barsm = P.box("live.menu", None, 1, 3, ["", "", "float"], (nx(), 700, 44, 15), pres=(570, 4, 40, 15),
                  **param("Bars", 2, 0, 4, 1, None, ["1", "2", "4", "8", "16"]))
    to_v8(barsm, "bars", x=ux, y=740)
    sbar = P.box("live.numbox", None, 1, 2, ["", "float"], (nx(), 700, 44, 15), pres=(614, 4, 44, 15),
                 **param("Bar", 1, 1, 999, 1, 0, shortname="Bar"))
    to_v8(sbar, "startbar", x=ux, y=740)
    seedb = P.box("live.numbox", None, 1, 2, ["", "float"], (nx(), 700, 50, 15), pres=(662, 4, 50, 15),
                  **param("Seed", 1, 0, 9999, 0, 0))
    to_v8(seedb, "seed", x=ux, y=740)
    phb = P.box("live.text", None, 1, 2, ["", ""], (nx(), 700, 56, 15), pres=(716, 4, 56, 15), mode=1,
                text="@Playhead", texton="@Playhead", **param("Playhead", 2, 0, 1, 0, None, ["off", "on"]))
    to_v8(phb, "playhead", x=ux, y=740)
    dials = [("Density", "density", 55), ("Chop", "chop", 55), ("Ghost", "ghost", 50), ("Roll", "roll", 35),
             ("Reverse", "reverse", 10), ("Swing", "swing", 0), ("Fill", "fill", 60), ("Strength", "strength", 55)]
    rdef = o("route " + " ".join(d[1] for d in dials), 1, len(dials) + 1, 700, 470, 360)
    P.wire(v8, 5, rdef, 0)
    for i, (lname, msgname, init) in enumerate(dials):
        d = P.box("live.dial", None, 2, 2, ["", "float"], (nx(50), 820, 44, 48),
                  pres=(474 + i * 49, 24, 44, 48), **param(lname, 0, 0.0, 100.0, float(init), 5))
        P.wire(rdef, i, d, 0)
        to_v8(d, msgname, x=ux, y=880)

    pitchd = P.box("live.dial", None, 2, 2, ["", "float"], (nx(50), 820, 44, 48), pres=(474, 80, 44, 48),
                   **param("Pitch", 0, -24.0, 24.0, 0.0, 7))
    to_v8(pitchd, "pitch", x=ux, y=880)
    lend = P.box("live.dial", None, 2, 2, ["", "float"], (nx(50), 820, 44, 48), pres=(523, 80, 44, 48),
                 **param("Length", 0, 10.0, 100.0, 100.0, 5))
    to_v8(lend, "slicelen", x=ux, y=880)
    chk = P.box("live.text", None, 1, 2, ["", ""], (nx(50), 820, 50, 15), pres=(574, 84, 56, 15), mode=1,
                text="Choke", texton="Choke", **param("Choke", 2, 0, 1, 1, None, ["off", "on"]))
    to_v8(chk, "choke", x=ux, y=880)
    syn = P.box("live.text", None, 1, 2, ["", ""], (nx(), 820, 50, 15), pres=(574, 104, 56, 15), mode=1,
                text="Sync", texton="Sync", **param("Sync", 2, 0, 1, 0, None, ["off", "on"]))
    to_v8(syn, "sync", x=ux, y=880)
    gen = P.box("live.text", None, 1, 2, ["", ""], (nx(), 820, 90, 36), pres=(640, 82, 132, 36), mode=0,
                text="Generate", **param("Generate", 2, 0, 1, None, None, ["off", "on"]))
    to_v8(gen, "generate", x=ux, y=880)
    tmp = P.box("live.text", None, 1, 2, ["", ""], (nx(), 820, 90, 15), pres=(776, 82, 88, 15), mode=0,
                text="Set Tempo", **param("Tempo", 2, 0, 1, None, None, ["off", "on"], shortname="Tempo"))
    to_v8(tmp, "tempo", x=ux, y=880)
    P.box("live.comment", None, 1, 0, None, (1200, 20, 150, 40), pres=(776, 100, 94, 40),
          text="C1–B4: slices\nC5+: reversed", textjustification=0, fontsize=9.0, linecount=2)

    return P.patcher(openinpresentation=1, devicewidth=916.0, title="BreakGen",
                     description="Sampling breakbeat generator")


def write_amxd(path, patch):
    data = json.dumps(patch, indent=1).encode("utf-8") + b"\n\x00"
    with open(path, "wb") as f:
        f.write(b"ampf" + struct.pack("<I", 4) + b"iiii" + b"meta" + struct.pack("<I", 4) + b"\x00" * 4)
        f.write(b"ptch" + struct.pack("<I", len(data)) + data)


if __name__ == "__main__":
    os.makedirs(INSTALL, exist_ok=True)
    os.makedirs(DOWNLOADS, exist_ok=True)
    build = os.path.join(HERE, "build")
    os.makedirs(build, exist_ok=True)
    write_amxd(os.path.join(build, "BreakGen.amxd"), build_device())
    with open(os.path.join(build, "bg_voice.maxpat"), "w") as f:
        json.dump(build_voice(), f, indent=1)
    shutil.copy(os.path.join(HERE, "breakgen.js"), build)
    for fn in ("BreakGen.amxd", "bg_voice.maxpat", "breakgen.js"):
        shutil.copy(os.path.join(build, fn), INSTALL)
    print("installed to", INSTALL)
