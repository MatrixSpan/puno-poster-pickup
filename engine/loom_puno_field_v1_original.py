# ======================================================================
# LOOM–PUNO reactive field — first functioning prototype
# Construction authorised (PUNO/KIP handover, construction gate open).
#
# ENVIRONMENT DECLARATION: stdlib-only (json). No network, no files,
# no subprocess, no credentials, no external writes. In-memory world;
# persistence = the serialized trace.
#
# STATUS: candidate implementation of a PUNO-inspired Reality.
# Laws are enforcement contracts, not possibility-maps
# (5D-policeman correction adopted). Situated engineering throughout.
# ======================================================================
import json

class Contraband(Exception):
    "Law violation at the consequence layer."

class FieldIntegrityError(Exception):
    "Replay mismatch: the trace and the published functions disagree."

class Addr:
    """Opaque condition handle. Law-layer minted at its trace position;
    replay-deterministic. Dialect discipline: opaque, unorderable,
    meaningless. Ordering of conditions is contraband."""
    __slots__ = ("_seq",)
    def __init__(self, seq): self._seq = seq
    def __eq__(self, o): return isinstance(o, Addr) and o._seq == self._seq
    def __hash__(self): return hash(("cond", self._seq))
    def __lt__(self, o): raise Contraband("ordering of conditions is contraband")
    def __repr__(self): return "\u25aa"

DECLARATION = ("Laws in the header are this implementation's declared "
    "consequence-sociology. They state what this Reality enforces and "
    "refuses. They do not state what is lawful, possible, or operative "
    "beyond the implementation (5D-policeman correction, adopted). "
    "Transformation, sequence, deterministic replay and fixed topology "
    "are situated engineering choices, not compulsory native properties.")

# ---- law-layer serialization: conditions cross as sealed tokens -------
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

# ---- the field ---------------------------------------------------------
class Field:
    def __init__(self, laws, dialects):
        self.laws = dict(laws)
        self.dialects = {}; self.participants = {}
        self.conditions = {}; self.trace = []; self._seq = 0
        self._event({"kind": "law-header", "laws": self.laws,
                     "dialects": sorted(dialects), "declaration": DECLARATION})
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
        ev = dict(ev); ev["seq"] = self._seq; self._seq += 1
        self.trace.append(ev); return ev

    def _mint(self):
        a = Addr(self._seq); self._seq += 1; return a

    # ---- L1: admission. Persist-and-address anything; interpret nothing.
    def admit(self, content, source, form_tag, route_to=None):
        dest = route_to or self.laws["default_recipient"]
        if dest not in self.dialects:
            raise Contraband("admission routed to an unregistered dialect")
        addr = self._mint()
        packet = {"content": content, "source": source, "form_tag": form_tag}
        self.conditions[addr] = {"kind": "encounter", "owner": source,
                                 "state": packet}
        self._event({"kind": "admission", "addrs": [addr], "addr": addr,
                     "packet": _ser(packet), "routed_to": dest,
                     "why": "threshold admission: persist-and-address, "
                            "interpret nothing"})
        self._deliver(addr, packet, dest)
        return addr

    # ---- L4: visibility filters access; never deletes.
    def _visible_tail(self, name):
        p = self.participants[name]
        if p.get("visibility") == "full": return list(self.trace)
        out = []
        for ev in self.trace:
            if ev.get("actor") == name or any(
                    a in p["encountered"] for a in ev.get("addrs", [])):
                out.append(ev)
        return out

    def _owned_states(self, name):
        return {a: c["state"] for a, c in self.conditions.items()
                if c.get("owner") == name}

    # ---- delivery: the law layer executes the published function --------
    def _deliver(self, addr, packet, dest):
        p = self.participants[dest]
        p["encountered"].add(addr)
        root = p["root"]
        own = self._owned_states(dest)
        encounter = {"packet": packet, "packet_addr": addr, "self_addr": root}
        tail = self._visible_tail(dest)
        mints = []
        mint = lambda init, why="": self._mint_for(dest, mints, init, why)
        new_own, acts = p["fn"](own, encounter, tail, mint)
        # L2/L3 enforcement: authority is ownership
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
                self.conditions[a]["state"] = st
                self._event({"kind": "transformation", "actor": dest,
                             "addrs": [a], "cond": a, "state": _ser(st)})
        for e in acts.get("expressions", []):
            self._event({"kind": "aperture", "actor": dest,
                         "addrs": [], "expression": e})
        for u in acts.get("unknowns", []):
            self._event({"kind": "unknown", "actor": dest,
                         "addrs": [u["about"]] if u.get("about") else [],
                         "about": u.get("about"), "reason": u.get("reason")})
        self._event({"kind": "note", "actor": dest, "addrs": [],
                     "why": acts.get("why", [])})

    def _mint_for(self, owner, mints, init, why):
        a = self._mint()
        self.conditions[a] = {"kind": "created", "owner": owner,
                              "state": _des(_ser(init))}
        mints.append((a, init, why))
        return a

    # ---- aperture-side delivery: meet a condition as-formed -------------
    def encounter_condition(self, participant, cond_addr):
        if cond_addr not in self.conditions:
            raise Contraband("condition does not exist")
        p = self.participants[participant]
        p["encountered"].add(cond_addr)
        packet = {"content": _ser(self.conditions[cond_addr].get("state")),
                  "source": "field", "form_tag": "condition-state"}
        self._event({"kind": "condition-encounter", "addrs": [cond_addr],
                     "addr": cond_addr, "to": participant, "packet": packet,
                     "why": "aperture delivery: as-formed, untranslated"})
        self._deliver(cond_addr, packet, participant)

    # ---- L5/L8: persistence and self-verifying replay -------------------
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
                f.admit(ev["packet"]["content"], ev["packet"]["source"],
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
    st = own.get(self_a)
    if st is None: st = {}
    st = _des(_ser(st))
    st.setdefault("arrivals", {}); st.setdefault("groups", {})
    st.setdefault("unknowns", []); st.setdefault("focus_map", {})
    pkt = encounter["packet"]; pid = encounter["packet_addr"]
    acts = {"expressions": [], "unknowns": [], "why": []}
    # registration is unconditional (L6: unresolved participation registers)
    st["arrivals"][pid] = {"form": pkt["form_tag"],
                           "source": pkt["provenance"]["source"]}
    acts["why"].append("L1 delivery: arrival registered unconditionally")
    if pkt["form_tag"] in KIP_FORMS:
        src = pkt["provenance"]["source"]
        grp = st["groups"].setdefault(src, [])
        if pid not in grp: grp.append(pid)
        acts["why"].append("dialect rule R2: same-source arrivals "
                           "grouped (order-free membership)")
        fmap = st["focus_map"]
        if src in fmap:
            fa = fmap[src]
            fstate = _des(_ser(own[fa]))
            fstate["arrivals_seen"] = fstate.get("arrivals_seen", 0) + 1
            new_own_fa = {fa: fstate}
            acts["why"].append("focus-condition updated (focus participates)")
        else:
            fstate = {"kind": "focus", "source": src, "arrivals_seen": 1}
            fa = mint(fstate, "focus-condition originated as field-matter")
            fmap[src] = fa
            new_own_fa = {}
            acts["why"].append("focus-condition originated as field-matter")
        acts["expressions"].append({"kind": "structural-summary",
            "registered": pid, "group": list(grp), "focus": fa})
    else:
        unk = {"about": pid,
               "reason": "form-tag '%s' not in this dialect" % pkt["form_tag"]}
        st["unknowns"].append(unk); acts["unknowns"].append(unk)
        acts["why"].append("L6: unresolved participation registered; "
                           "UNKNOWN marked, not rescued")
    new_own = dict(own); new_own[self_a] = st; new_own.update(new_own_fa)
    return new_own, acts
kip_respond.declaration = KIP_DECLARATION

# ---- L: minimal second-locus stub (differently situated) ---------------
def l_respond(own, encounter, tail, mint):
    self_a = encounter["self_addr"]
    st = own.get(self_a)
    if st is None: st = {}
    st = _des(_ser(st))
    st.setdefault("encounters", [])
    st["encounters"] = list(st["encounters"]) + [{
        "packet_addr": encounter["packet_addr"],
        "form": encounter["packet"]["form_tag"],
        "content": encounter["packet"]["content"]}]
    acts = {"expressions": [], "unknowns": [],
            "why": ["received; stub retains as-formed, untranslated"]}
    return {self_a: st}, acts
l_respond.declaration = "stub: receives, retains as-formed, interprets nothing"

LAWS = {
    "declaration": DECLARATION,
    "default_recipient": "KIP",
    "L1": "admission routes per tag or default recipient",
    "L2": "self-and-owned transformation only; encounters are reads",
    "L3": "trace is the shared medium; visibility per participant",
    "L4": "visibility filters access, never deletes",
    "L5": "trace append-only, verbatim",
    "L6": "UNKNOWN distinct from refusal and absence",
    "L7": "zero external writes; aperture exposes expressions only",
    "L8": "field-state replay-derivable from trace + published functions",
}
