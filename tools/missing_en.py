from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from rdflib import Graph, Literal


@dataclass(frozen=True)
class MissingLang:
    subject: str
    predicate: str
    pt_br: str


def main() -> int:
    g = Graph()
    path = "/Users/eliasmpjunior/my-desktop/projects/kb-elias/nid/elias.ttl"
    g.parse(path, format="turtle")

    langs: dict[tuple[str, str], set[str]] = defaultdict(set)
    pt_vals: dict[tuple[str, str], list[str]] = defaultdict(list)

    for s, p, o in g:
        if isinstance(o, Literal) and o.language:
            key = (str(s), str(p))
            lang = o.language.lower()
            langs[key].add(lang)
            if lang == "pt-br":
                pt_vals[key].append(str(o))

    missing: list[MissingLang] = []
    for (s, p), ls in langs.items():
        if "pt-br" in ls and "en" not in ls:
            pts = pt_vals.get((s, p), [])
            if pts:
                missing.append(MissingLang(subject=s, predicate=p, pt_br=pts[0]))

    missing.sort(key=lambda x: (x.predicate, x.subject))
    print("pairs_with_ptbr_but_no_en:", len(missing))
    for i, item in enumerate(missing, 1):
        print(f"--- {i} ---")
        print("S", item.subject)
        print("P", item.predicate)
        print("PT", item.pt_br.replace("\n", "\\n"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
