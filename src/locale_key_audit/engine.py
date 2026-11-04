"""Implement the exact README contract; no I/O or operational effects."""

def _is_tag(t):
    if type(t) is not str:
        return False
    n = len(t)
    if n < 1 or n > 35:
        return False
    o = ord(t[0])
    if not ((65 <= o <= 90) or (97 <= o <= 122)):
        return False
    for ch in t[1:]:
        o = ord(ch)
        if not ((65 <= o <= 90) or (97 <= o <= 122) or (48 <= o <= 57) or o == 45):
            return False
    return True

def _collect(root):
    if type(root) is not dict:
        raise ValueError
    paths = set()
    count = 1
    if len(root) == 0:
        return paths
    try:
        first = list(root.items())
    except Exception:
        raise ValueError
    ancestors = {id(root)}
    stack = [[root, 0, first, 0, []]]
    while stack:
        frame = stack[-1]
        obj = frame[0]
        depth = frame[1]
        items = frame[2]
        idx = frame[3]
        prefix = frame[4]
        if idx >= len(items):
            ancestors.discard(id(obj))
            stack.pop()
            continue
        k, v = items[idx]
        frame[3] = idx + 1
        if type(k) is not str:
            raise ValueError
        kl = len(k)
        if kl < 1 or kl > 80:
            raise ValueError
        for ch in k:
            o = ord(ch)
            if o < 32 or 55296 <= o <= 57343:
                raise ValueError
        cd = depth + 1
        if cd > 12:
            raise ValueError
        ek = k.replace("~", "~0").replace("/", "~1")
        tv = type(v)
        if tv is dict:
            count += 1
            if count > 10000:
                raise ValueError
            if id(v) in ancestors:
                raise ValueError
            ancestors.add(id(v))
            try:
                child = list(v.items())
            except Exception:
                raise ValueError
            stack.append([v, cd, child, 0, prefix + [ek]])
        elif tv is str:
            count += 1
            if count > 10000:
                raise ValueError
            if len(v) > 2000:
                raise ValueError
            for ch in v:
                o = ord(ch)
                if 55296 <= o <= 57343:
                    raise ValueError
                if o < 32 and o != 9 and o != 10 and o != 13:
                    raise ValueError
            if prefix:
                paths.add("/" + "/".join(prefix + [ek]))
            else:
                paths.add("/" + ek)
        else:
            raise ValueError
    return paths

def analyze(payload):
    try:
        if type(payload) is not dict:
            raise ValueError("INPUT_INVALID")
        try:
            keys = set(payload.keys())
        except Exception:
            raise ValueError("INPUT_INVALID")
        if keys != {"reference", "locales"}:
            raise ValueError("INPUT_INVALID")
        ref = payload["reference"]
        locs = payload["locales"]
        if type(ref) is not dict:
            raise ValueError("INPUT_INVALID")
        if type(locs) is not dict:
            raise ValueError("INPUT_INVALID")
        if len(locs) > 20:
            raise ValueError("INPUT_INVALID")
        try:
            pairs = list(locs.items())
        except Exception:
            raise ValueError("INPUT_INVALID")
        for tg, cat in pairs:
            if not _is_tag(tg):
                raise ValueError("INPUT_INVALID")
            if type(cat) is not dict:
                raise ValueError("INPUT_INVALID")
        try:
            ref_paths = _collect(ref)
        except Exception:
            raise ValueError("INPUT_INVALID")
        loc_map = {}
        for tg, cat in pairs:
            try:
                loc_map[tg] = _collect(cat)
            except Exception:
                raise ValueError("INPUT_INVALID")
        out = []
        for tg in sorted(loc_map.keys()):
            lp = loc_map[tg]
            missing = sorted(ref_paths - lp)
            extra = sorted(lp - ref_paths)
            matched = len(ref_paths & lp)
            out.append({"locale": tg, "missing": missing, "extra": extra, "matched": matched})
        valid = True
        for e in out:
            if e["missing"] or e["extra"]:
                valid = False
                break
        return {"valid": valid, "reference_keys": len(ref_paths), "locales": out}
    except ValueError as ex:
        if str(ex) == "INPUT_INVALID":
            raise
        raise ValueError("INPUT_INVALID")
    except Exception:
        raise ValueError("INPUT_INVALID")
