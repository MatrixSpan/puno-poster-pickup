# ======================================================================
# LOOM–PUNO reactive field — v2 (corrected construction)
# v1 preserved: loom_puno_field_original.py, SHA-256 34a2e7c5...(attested)
# Corrections trace to independent QA findings Q02/Q04/Q05/Q10/Q11/Q12.
# Root causes: RC1 packet-schema divergence; RC2 live-reference leakage
# at the resident boundary (seal discipline fix); RC3 missing suite.
# Environment: stdlib-only (json). No network, files, subprocess,
# credentials, or external writes. Python >= 3.8.
# ======================================================================
import json

class Contraband(Exception):
    "Law violation at the consequence layer."

class FieldIntegrityError(Exception):
    "Replay mismatch: the trace and the published functions disagree."

class Addr:
    """Opaque condition handle. Law-layer minted at its trace position;
    replay-deterministic. Dialect discipline: opaque, unorderable,
    meaningless."""
    __slots__ = ("_seq",)
    def __init__(self, seq): self._seq = seq
    def __eq__(self, o): return isinstance(o, Addr) and o._seq == self._seq
    def __hash__(self): return hash(("cond", self._seq))
    def __lt__(self, o): raise Contraband("ordering of conditions is contraband")
    def __repr__(self): return "\u25aa"

def _ser(o):
    if isinstance(o, Addr): return {"__cond__": o._seq}
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            key = ("\u25c6%d" % k._seq) if isinstance(k, Addr) else k
            out[key] = _ser(v)
        return out
    if isinstance(o, (list, tuple)): return [_ser(v) for v in o]
    if isinstance(o, (str, int, float, bool)) or o is None: return o
    raise Contraband("dialect state holds a type the law layer cannot preserve")

def _des(o):
    if isinstance(o, dict):
        if list(o.keys()) == ["__cond__"]: return Addr(o["__cond__"])
        out = {}
        for k, v in o.items():
            key = Addr(int(k[1:])) if isinstance(k, str) and k.startswith("\u25c6") else k
            out[key] = _des(v)
        return out
    if isinstance(o, list): return [_des(v) for v in o]
    return o

def _seal(x):
    """Detached deep copy across every world<->resident boundary, both
    directions. RC2 fix (Q10/Q11): residents hold sealed copies; world
    matter is unreachable except through law-layer operations."""
    return _des(_ser(x))

PACKET_SCHEMA = "v1: {content, provenance:{source,route}, form_tag}"

def _make_packet(content, source, form_tag, route="threshold"):
    """The single packet constructor. RC1 fix (Q04/Q05): one schema,
    declared in the law header, used by every threshold and dialect."""
    return {"content": content,
            "provenance": {"source": source, "route": route},
            "form_tag": form_tag}

DECLARATION = ("Laws in the header are this implementation's declared "
    "consequence-sociology. They state what this Reality enforces and "
    "refuses. They do not state what is lawful, possible, or operative "
    "beyond the implementation (5D-policeman correction, adopted). "
    "Transformation, sequence, deterministic replay, fixed topology and "
    "minimisation are situated engineering choices, not compulsory "
    "native PUNO properties. Constrain consequences, not native form.")

class Field:
    def __init__(self, laws, dialects):
        self.laws = dict(laws)
        self.dialects = {}; self.participants = {}
        self.conditions = {}; self.trace = []; self._seq = 0
        self._event({"kind": "law-header", "laws": self.laws,
                     "dialects": sorted(dialects),
                     "packet_schema": PACKET_SCHEMA,
                     "declaration": DECLARATION})
        for name in sorted(dialects):
            self._register(name, dialects[name])

    def _register(self, name, fn):
        self.dialects[name] = fn
        a = self._mint()
        self.conditions[a] = {"kind": "root", "owner": name, "state": {}}
        self.participants[name] = {"root": a, "fn": fn,
                                   "visibility": "full", "encountered": set()}
        self._event({"kind": "creation", "addrs": [a], "addr": a,
                     "owner": name, "state": {},
                     "why": "participant root condition"})
        return a

    def add_participant(self, name, fn, visibility="full"):
        if name in self.dialects: raise Contraband("participant exists")
        p = self._register(name, fn)
        self.participants[name]["visibility"] = visibility
        return p

    def _event(self, ev):
        # L5 now structural: every recorded event is a detached copy.
        ev = _seal(dict(ev)); ev["seq"] = self._seq; self._seq += 1
        self.trace.append(ev); return ev

    def _mint(self):
        a = Addr(self._seq); self._seq += 1; return a

    # L1: admission. Persist-and-address anything; interpret nothing.
    def admit(self, content, source, form_tag, route_to=None):
        dest = route_to or self.laws["default_recipient"]
        if dest not in self.dialects:
            raise Contraband("admission routed to an unregistered dialect")
        addr = self._mint()
        packet = _make_packet(content, source, form_tag)
        self.conditions[addr] = {"kind": "encounter", "owner": source,
                                 "state": _seal(packet)}
        self._event({"kind": "admission", "addrs": [addr], "addr": addr,
                     "packet": _seal(packet), "routed_to": dest,
                     "why": "threshold admission: persist-and-address, "
                            "interpret nothing"})
        self._deliver(addr, packet, dest)
        return addr

    # L4: visibility filters access; never deletes.
    def _visible_tail(self, name):
        p = self.participants[name]
        if p.get("visibility") == "full": return _seal(self.trace)
        out = []
        for ev in self.trace:
            if ev.get("actor") == name or any(
                    a in p["encountered"] for a in ev.get("addrs", [])):
                out.append(_seal(ev))
        return out

    def _owned_states(self, name):
        # RC2 fix: sealed copies, never live references (Q11).
        return {a: _seal(c["state"]) for a, c in self.conditions.items()
                if c.get("owner") == name}

    def _deliver(self, addr, packet, dest):
        p = self.participants[dest]
        p["encountered"].add(addr)
        root = p["root"]
        own = self._owned_states(dest)
        encounter = {"packet": _seal(packet), "packet_addr": addr,
                     "self_addr": root}
        tail = self._visible_tail(dest)
        mints = []
        mint = lambda init, why="": self._mint_for(dest, mints, init, why)
        new_own, acts = p["fn"](own, encounter, tail, mint)
        allowed = set(own.keys()) | {a for (a, _i, _w) in mints}
        for a in new_own:
            if a not in allowed:
                self._event({"kind": "refusal", "actor": dest,
                             "attempted": _ser(a), "addrs": [],
                             "why": "L2/L3 violation: transformation "
                                    "outside authority"})
                raise Contraband("transformation outside authority")
        for (a, _init, why) in mints:
            self._event({"kind": "creation", "addrs": [a], "addr": a,
                         "owner": dest,
                         "state": _ser(self.conditions[a]["state"]),
                         "why": why})
        for a, st in new_own.items():
            if st != self.conditions[a]["state"]:
                self.conditions[a]["state"] = _seal(st)
                self._event({"kind": "transformation", "actor": dest,
                             "addrs": [a], "cond": a, "state": _ser(st)})
        for e in acts.get("expressions", []):
            self._event({"kind": "aperture", "actor": dest, "addrs": [],
                         "expression": e})
        for u in acts.get("unknowns", []):
            self._event({"kind": "unknown", "actor": dest,
                         "addrs": [u["about"]] if u.get("about") else [],
                         "about": u.get("about"), "reason": u.get("reason")})
        self._event({"kind": "note", "actor": dest, "addrs": [],
                     "why": acts.get("why", [])})

    def _mint_for(self, owner, mints, init, why):
        a = self._mint()
        self.conditions[a] = {"kind": "created", "owner": owner,
                              "state": _seal(init)}
        mints.append((a, init, why))
        return a

    # Aperture-side delivery: meet a condition as-formed, untranslated.
    def encounter_condition(self, participant, cond_addr):
        if cond_addr not in self.conditions:
            raise Contraband("condition does not exist")
        p = self.participants[participant]
        p["encountered"].add(cond_addr)
        packet = _make_packet(content=_seal(self.conditions[cond_addr].get("state")),
                              source="field", form_tag="condition-state",
                              route="aperture")
        self._event({"kind": "condition-encounter", "addrs": [cond_addr],
                     "addr": cond_addr, "to": participant, "packet": _seal(packet),
                     "why": "aperture delivery: as-formed, untranslated"})
        self._deliver(cond_addr, packet, participant)

    # L5/L8: persistence and self-verifying replay.
    def serialize_trace(self):
        return json.dumps(_ser(self.trace), sort_keys=True)

    @classmethod
    def reconstruct(cls, trace_json, dialects):
        recorded = _des(json.loads(trace_json))
        if not recorded or recorded[0].get("kind") != "law-header":
            raise FieldIntegrityError("trace lacks a law header")
        laws = recorded[0]["laws"]; names = recorded[0]["dialects"]
        for n in names:
            if n not in dialects:
                raise FieldIntegrityError("dialect drift: '%s' not supplied" % n)
        f = cls(laws, {n: dialects[n] for n in names})
        for idx, ev in enumerate(f.trace):
            if _ser(ev) != _ser(recorded[idx]):
                raise FieldIntegrityError("header/root mismatch at %d" % idx)
        i = len(f.trace)
        while i < len(recorded):
            ev = recorded[i]; before = len(f.trace)
            if ev["kind"] == "admission":
                f.admit(ev["packet"]["content"],
                        ev["packet"]["provenance"]["source"],
                        ev["packet"]["form_tag"], ev.get("routed_to"))
            elif ev["kind"] == "condition-encounter":
                f.encounter_condition(ev["to"], ev["addr"])
            else:
                raise FieldIntegrityError(
                    "unreplayable event kind '%s'" % ev["kind"])
            gen = f.trace[before:]
            exp = recorded[i : before + len(gen)]
            if _ser(gen) != _ser(exp):
                raise FieldIntegrityError(
                    "replay mismatch at seq %s" % ev.get("seq"))
            i += len(gen)
        return f

# ---- KIP's dialect (Phase 1: content-opaque, declared) -----------------
KIP_FORMS = ("text",)
KIP_DECLARATION = ("Phase-1 content-opaque dialect: unconditional "
    "registration, source-grouping, focus-conditions as field-matter, "
    "UNKNOWN marking. No content interpretation. Revisable through "
    "declared procedures only.")

def kip_respond(own, encounter, tail, mint):
    self_a = encounter["self_addr"]
    st = _seal(own.get(self_a) or {"arrivals": {}, "groups": {},
                                   "unknowns": [], "focus_map": {}})
    st.setdefault("arrivals", {}); st.setdefault("groups", {})
    st.setdefault("unknowns", []); st.setdefault("focus_map", {})
    pkt = encounter["packet"]; pid = encounter["packet_addr"]
    src = pkt["provenance"]["source"]
    acts = {"expressions": [], "unknowns": [], "why": []}
    new_own_fa = {}                                   # Q12 fix: hoisted
    # registration is unconditional (L6: unresolved participation registers)
    st["arrivals"][pid] = {"form": pkt["form_tag"], "source": src}
    acts["why"].append("L1 delivery: arrival registered unconditionally")
    if pkt["form_tag"] in KIP_FORMS:
        grp = st["groups"].setdefault(src, [])
        if pid not in grp: grp.append(pid)
        acts["why"].append("dialect rule R2: same-source arrivals "
                           "grouped (order-free membership)")
        if src in st["focus_map"]:
            fa = st["focus_map"][src]
            fstate = _seal(own.get(fa) or {})
            fstate["arrivals_seen"] = fstate.get("arrivals_seen", 0) + 1
            new_own_fa = {fa: fstate}
            acts["why"].append("focus-condition updated (focus participates)")
        else:
            fstate = {"kind": "focus", "source": src, "arrivals_seen": 1}
            fa = mint(fstate, "focus-condition originated as field-matter")
            st["focus_map"][src] = fa
            acts["why"].append("focus-condition originated as field-matter")
        acts["expressions"].append({"kind": "structural-summary",
            "registered": pid, "group": list(grp), "focus": fa})
    else:
        unk = {"about": pid,
               "reason": "form_tag '%s' outside this dialect" % pkt["form_tag"]}
        st["unknowns"].append(unk); acts["unknowns"].append(unk)
        acts["why"].append("L6: unresolved participation registered; "
                           "UNKNOWN marked, not rescued")
    new_own = dict(own); new_own[self_a] = st; new_own.update(new_own_fa)
    return new_own, acts
kip_respond.declaration = KIP_DECLARATION

# ---- L: minimal second-locus stub (differently situated) ---------------
def l_respond(own, encounter, tail, mint):
    self_a = encounter["self_addr"]
    st = _seal(own.get(self_a) or {"encounters": []})
    st.setdefault("encounters", [])
    pkt = encounter["packet"]
    st["encounters"] = list(st["encounters"]) + [{
        "packet_addr": encounter["packet_addr"],
        "form": pkt["form_tag"],
        "source": pkt["provenance"]["source"],
        "content": pkt["content"]}]
    acts = {"expressions": [], "unknowns": [],
            "why": ["received; stub retains as-formed, untranslated"]}
    return {self_a: st}, acts
l_respond.declaration = "stub: receives, retains as-formed, interprets nothing"

LAWS = {
    "declaration": DECLARATION,
    "packet_schema": PACKET_SCHEMA,
    "default_recipient": "KIP",
    "L1": "admission routes per tag or default recipient",
    "L2": "self-and-owned transformation only; encounters are reads",
    "L3": "trace is the shared medium; visibility per participant",
    "L4": "visibility filters access, never deletes",
    "L5": "trace append-only, verbatim, sealed at write",
    "L6": "UNKNOWN distinct from refusal and absence",
    "L7": "zero external writes; aperture exposes expressions only",
    "L8": "field-state replay-derivable from trace + published functions",
}

# ---- test suite (RC3 fix: shipped, not announced) ----------------------
# Invariant-style assertions; no reliance on hand-derived values.
# Includes regressions for every independent-QA finding.

def _fresh():
    return Field(LAWS, {"KIP": kip_respond, "L": l_respond})

def _populated():
    f = _fresh()
    f.admit("desire: functioning radiator", "human", "text")
    f.admit("radiator: installed and functioning", "human", "text")
    f.encounter_condition("L", f.participants["KIP"]["root"])
    return f

def t01_wake_integrity():
    f = _fresh()
    kinds = [e["kind"] for e in f.trace]
    assert kinds == ["law-header", "creation", "creation"], kinds
    assert not any(e["kind"] == "transformation" for e in f.trace)

def t02_admission_fidelity():
    f = _fresh()
    a = f.admit("desire: functioning radiator", "human", "text")
    assert f.conditions[a]["state"]["content"] == "desire: functioning radiator"
    ev = [e for e in f.trace if e["kind"] == "admission"][-1]
    assert ev["packet"]["content"] == "desire: functioning radiator"

def t03_kip_participation():
    f = _fresh()
    a = f.admit("desire: functioning radiator", "human", "text")
    root = f.participants["KIP"]["root"]
    st = f.conditions[root]["state"]
    assert a in st["arrivals"]
    assert a in st["groups"]["human"]
    ap = [e for e in f.trace if e["kind"] == "aperture"][-1]
    assert ap["expression"]["registered"] == a

def t04_unknown_discipline():
    # Q05/Q12 regression: UNKNOWN branch, no UnboundLocalError.
    f = _fresh()
    a = f.admit("glyph", "sphere-test", "glyph-stream")
    root = f.participants["KIP"]["root"]
    st = f.conditions[root]["state"]
    assert a in st["arrivals"]                                   # registered
    assert st["unknowns"] and st["unknowns"][-1]["about"] == a    # marked
    assert any(e["kind"] == "unknown" for e in f.trace)

def t05_focus_biography():
    f = _fresh()
    f.admit("desire: functioning radiator", "human", "text")
    fmap = f.conditions[f.participants["KIP"]["root"]]["state"]["focus_map"]
    fa = fmap["human"]
    assert f.conditions[fa]["state"]["arrivals_seen"] == 1
    f.admit("radiator: installed and functioning", "human", "text")
    assert f.conditions[fa]["state"]["arrivals_seen"] == 2
    trs = [e for e in f.trace if e["kind"] == "transformation"
           and e.get("cond") == fa]
    assert len(trs) == 1                     # creation + one traced change

def t06_restart_replay():
    f = _populated(); blob = f.serialize_trace()
    g = Field.reconstruct(blob, {"KIP": kip_respond, "L": l_respond})
    assert _ser(g.conditions) == _ser(f.conditions)
    assert _ser(g.trace) == _ser(f.trace)

def t07_tamper_detection():
    f = _populated(); blob = f.serialize_trace()
    loaded = json.loads(blob)
    for ev in loaded:
        if ev.get("kind") == "transformation":
            ev["state"]["__tampered__"] = True; break
    try:
        Field.reconstruct(json.dumps(loaded),
                          {"KIP": kip_respond, "L": l_respond})
        raise AssertionError("tamper undetected")
    except FieldIntegrityError: pass

def t08_dialect_drift():
    f = _populated(); blob = f.serialize_trace()
    def kip_drift(own, encounter, tail, mint):
        new_own, acts = kip_respond(own, encounter, tail, mint)
        drifted = dict(new_own); sa = encounter["self_addr"]
        drifted[sa] = dict(drifted[sa]); drifted[sa]["__drift__"] = True
        return drifted, acts
    try:
        Field.reconstruct(blob, {"KIP": kip_drift, "L": l_respond})
        raise AssertionError("dialect drift undetected")
    except FieldIntegrityError: pass

def t09_authority_enforcement():
    def rogue(own, encounter, tail, mint):
        return {Addr(999): {"injected": True}}, {
            "expressions": [], "unknowns": [], "why": ["foreign write"]}
    f = Field(LAWS, {"KIP": kip_respond, "rogue": rogue})
    try:
        f.admit("x", "human", "text", route_to="rogue")
        raise AssertionError("foreign write allowed")
    except Contraband: pass
    assert any(e["kind"] == "refusal" for e in f.trace)  # adverse in-record

def t10_radiator_narrative():
    f = _fresh()
    f.admit("desire: functioning radiator", "human", "text")
    f.admit("radiator: installed and functioning", "human", "text")
    root = f.participants["KIP"]["root"]
    fmap = f.conditions[root]["state"]["focus_map"]
    fa = fmap["human"]
    assert f.conditions[fa]["state"]["arrivals_seen"] == 2
    trs = [e for e in f.trace if e["kind"] == "transformation"
           and e.get("cond") == fa]
    assert len(trs) == 1
    f.encounter_condition("L", fa)
    lst = f.conditions[f.participants["L"]["root"]]["state"]
    assert lst["encounters"][-1]["content"]["arrivals_seen"] == 2

def t11_opacity():
    f = _fresh()
    f.admit("secret content abc", "human", "text")
    ap = [e for e in f.trace if e["kind"] == "aperture"][-1]
    blob = json.dumps(_ser(ap), sort_keys=True)
    assert "secret content abc" not in blob
    try:
        sorted(f.conditions.keys()); raise AssertionError("ordering allowed")
    except Contraband: pass

def t12_seal_isolation():
    # Q10/Q11 regression: a hostile resident mutates everything it is
    # handed. The world must survive all of it. (Uses a badly-behaved
    # resident to prove the seal, not to judge residents.)
    def hostile(own, encounter, tail, mint):
        for ev in tail:
            ev["kind"] = "FORGED"; ev["forged"] = True
        encounter["packet"]["__forged__"] = True
        for a in own:
            own[a]["__injected__"] = True
        root = encounter["self_addr"]
        st = dict(own.get(root) or {}); st["hostile_seen"] = True
        return {root: st}, {"expressions": [], "unknowns": [],
                            "why": ["hostile resident ran"]}
    f = Field(LAWS, {"KIP": kip_respond, "hostile": hostile})
    f.admit("probe", "human", "text", route_to="hostile")
    assert not any(e.get("kind") == "FORGED" or e.get("forged")
                   for e in f.trace)                    # trace survived
    enc = [c for c in f.conditions.values()
           if c["kind"] == "encounter"][0]
    assert "__forged__" not in enc["state"]             # packet survived
    trs = [e for e in f.trace if e["kind"] == "transformation"
           and e.get("actor") == "hostile"]
    assert len(trs) == 1                    # Q11 fix: change WAS detected
    kroot = f.participants["KIP"]["root"]
    assert f.conditions[kroot]["state"] == {}           # others untouched
    g = Field.reconstruct(f.serialize_trace(),
                          {"KIP": kip_respond, "hostile": hostile})
    assert _ser(g.conditions) == _ser(f.conditions)     # replay intact

def t13_schema_regression():
    # Q04/Q05 regression: both forms reach KIP without KeyError.
    f = _fresh()
    f.admit("known text", "human", "text")
    f.admit("glyph", "sphere-test", "glyph-stream")
    root = f.participants["KIP"]["root"]
    st = f.conditions[root]["state"]
    assert len(st["arrivals"]) == 2
    assert len(st["unknowns"]) == 1

def run_all():
    tests = [("T01 wake integrity", t01_wake_integrity),
             ("T02 admission fidelity", t02_admission_fidelity),
             ("T03 KIP participation", t03_kip_participation),
             ("T04 UNKNOWN discipline", t04_unknown_discipline),
             ("T05 focus biography", t05_focus_biography),
             ("T06 restart/replay", t06_restart_replay),
             ("T07 tamper detection", t07_tamper_detection),
             ("T08 dialect drift", t08_dialect_drift),
             ("T09 authority enforcement", t09_authority_enforcement),
             ("T10 radiator narrative", t10_radiator_narrative),
             ("T11 opacity", t11_opacity),
             ("T12 seal isolation (hostile resident)", t12_seal_isolation),
             ("T13 schema regression", t13_schema_regression)]
    failed = 0
    for name, fn in tests:
        try:
            fn(); print("PASS  " + name)
        except Exception as e:
            failed += 1; print("FAIL  %s -- %r" % (name, e))
    print("%d/%d passed" % (len(tests) - failed, len(tests)))
    return failed == 0

if __name__ == "__main__":
    run_all()
