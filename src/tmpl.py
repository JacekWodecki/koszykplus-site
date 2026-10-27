"""Minimalny system szablonów (stdlib). Składnia:

  {{ sciezka.do.klucza }}          -> tekst z escapowaniem HTML
  {{ klucz|rich }}                 -> tekst z mini-znacznikami (patrz rich())
  {{ klucz|title }}                -> jak rich, ale także \\n -> <br> i *akcent* -> <em>
  {{ klucz|raw }}                  -> wstawione bez zmian (tylko wartości liczone przez build.py)
  {% for x in lista %}...{% endfor %}   (w pętli: loop.index, loop.first, loop.last)
  {% if klucz %}...{% else %}...{% endif %}   ({% if not klucz %} także)

Brakujący klucz = błąd budowania (brak cichych pustych miejsc).
"""
import html
import re

TOKEN = re.compile(r"(\{\{.*?\}\}|\{%.*?%\})", re.S)


class TemplateError(Exception):
    pass


def lookup(ctx, path):
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict):
            if part not in cur:
                raise TemplateError("brak klucza: " + path)
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        else:
            raise TemplateError("nie można odczytać %r w %r" % (part, path))
    return cur


def esc(s):
    return html.escape(str(s), quote=True)


LINK_RE = re.compile(r"\[\[(.+?)\|([a-z_]+)\]\]")


def rich(text, links, br=False, em=False):
    """Mini-znaczniki w tłumaczeniach:
    [[etykieta|nazwa]] -> <a href=links[nazwa]>etykieta</a>;  **tekst** -> <strong>;
    (title) \\n -> <br>, *tekst* -> <em>.  Cały pozostały tekst jest escapowany."""
    out = esc(text)
    def link(m):
        name = m.group(2)
        if name not in links:
            raise TemplateError("nieznany link [[%s]]" % name)
        href = links[name]
        ext = ' rel="external"' if href.startswith("http") else ""
        return '<a href="%s"%s>%s</a>' % (href, ext, m.group(1))
    out = LINK_RE.sub(link, out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    if em:
        out = re.sub(r"\*(.+?)\*", r"<em>\1</em>", out)
    if br:
        out = out.replace("\n", "<br>")
    return out


def parse(src):
    tokens = [t for t in TOKEN.split(src) if t != ""]
    pos = 0

    def block(stop):
        nonlocal pos
        nodes = []
        while pos < len(tokens):
            t = tokens[pos]
            if t.startswith("{%"):
                tag = t[2:-2].strip()
                head = tag.split(None, 1)[0]
                if head in stop:
                    return nodes, tag
                pos += 1
                if head == "for":
                    m = re.match(r"for\s+(\w+)\s+in\s+([\w.]+)$", tag)
                    if not m:
                        raise TemplateError("zła składnia: " + tag)
                    body, end = block(("endfor",))
                    pos += 1
                    nodes.append(("for", m.group(1), m.group(2), body))
                elif head == "if":
                    cond = tag[2:].strip()
                    neg = cond.startswith("not ")
                    if neg:
                        cond = cond[4:].strip()
                    body, end = block(("else", "endif"))
                    pos += 1
                    other = []
                    if end == "else":
                        other, end = block(("endif",))
                        pos += 1
                    nodes.append(("if", neg, cond, body, other))
                else:
                    raise TemplateError("nieznany tag: " + tag)
            elif t.startswith("{{"):
                expr = t[2:-2].strip()
                name, _, flt = expr.partition("|")
                nodes.append(("var", name.strip(), flt.strip()))
                pos += 1
            else:
                nodes.append(("text", t))
                pos += 1
        if stop:
            raise TemplateError("brak zamknięcia bloku: " + "/".join(stop))
        return nodes, None

    nodes, _ = block(())
    return nodes


def render_nodes(nodes, ctx):
    out = []
    for n in nodes:
        kind = n[0]
        if kind == "text":
            out.append(n[1])
        elif kind == "var":
            val = lookup(ctx, n[1])
            flt = n[2]
            if flt == "raw":
                out.append(str(val))
            elif flt == "rich":
                out.append(rich(val, ctx["links"], br=True))
            elif flt == "title":
                out.append(rich(val, ctx["links"], br=True, em=True))
            elif flt == "":
                out.append(esc(val))
            else:
                raise TemplateError("nieznany filtr: " + flt)
        elif kind == "for":
            seq = lookup(ctx, n[2])
            for i, item in enumerate(seq):
                sub = dict(ctx)
                sub[n[1]] = item
                sub["loop"] = {"index": i + 1, "first": i == 0, "last": i == len(seq) - 1}
                out.append(render_nodes(n[3], sub))
        elif kind == "if":
            val = lookup(ctx, n[2])
            ok = bool(val)
            if n[1]:
                ok = not ok
            out.append(render_nodes(n[3] if ok else n[4], ctx))
    return "".join(out)


def render(src, ctx):
    return render_nodes(parse(src), ctx)
