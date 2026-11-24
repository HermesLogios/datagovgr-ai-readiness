r"""
17_hvd_broad_reading.py
Phase 3, step 8: what the broad reading of point 2.1 of the Annex of Implementing Regulation (EU) 2023/138 would add to
the high-value datasets of the portal, part 4b of the gap analysis (DECISIONS.md #17 and #62).

What it does, in order:
  1. Reads the map layers that the portal harvests from the GIS servers of public bodies (the datasets of the catalogue
     snapshot whose name begins with "gis-"), the high-value marking of each from the table of 04_metadata_checks.py, and
     the search patterns of the datasets of the Annex (criteria/hvd_annex_items.csv) for points 1.1, 2.1 and 6.1.
  2. Places every layer in one group, by its title and the name of its source:
       - both readings: its content belongs to a theme or domain of the Annex (an orthophoto, a land use zone, a
         stream, a road network), so that it is high-value by content under the narrow reading as well;
       - broad reading only: a scanned sheet of a single legal act (a town-plan amendment, the delimitation of a
         settlement) or other environmental information outside the themes, which the clause of point 2.1 on all the
         environmental information of Directive 2003/4/EC would add;
       - neither: the other layers (points of interest, services, values of property).
     The first rule that applies decides: orthophotos and aerial photographs; then scans of legal acts (a sheet number
     of the Government Gazette or a raster of the street plan in the name of the source, or a raster or a map view
     whose title names a legal act or a plan); then local estimates of emissions and the collection of waste by a
     municipality (bins, routes), which are environmental information but not the data of the legal acts that the
     second table of point 2.1 names; then the patterns of the Annex, completed with terms of the map layers
     (LAYER_TERMS); then other layers whose title names a legal act or a plan; then environmental terms.
  3. Draws 10 layers of each group at random, with a fixed seed, for a check by the reviewer; where the judgement of the
     reviewer is recorded (criteria/hvd_broad_reading_check.csv), reports the agreement of the rule in each group and
     the layers on which the two differ.
  4. Writes:
       - data/processed/hvd_broad_reading_YYYY-MM-DD.csv, one row per layer with its group and the rule that placed it,
         without its title, since the title of the scan of an act on a single property can name its owner;
       - data/processed/hvd_broad_reading_sample_YYYY-MM-DD.csv, the layers of the check;
       - outputs/hvd_broad_reading_YYYY-MM-DD/summary.md.

Rules:
  - A group is a measurement by rule, not a judgement of each layer; the check of the sample measures its accuracy.
  - Only the metadata of the snapshot are read; no request is sent to the portal or to any other site.

Usage (from the project root, with the .venv activated):
    python scripts\17_hvd_broad_reading.py

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
ITEMS_FILE = ROOT / "criteria" / "hvd_annex_items.csv"
CHECK_FILE = ROOT / "criteria" / "hvd_broad_reading_check.csv"
PORTAL = "https://data.gov.gr"

HARVEST_PREFIX = "gis-"
MAP_VIEW_ONLY = "-wms-only-"
BOTH, BROAD, NEITHER = "both readings", "broad reading only", "neither"
GROUPS = (BOTH, BROAD, NEITHER)
THEME_POINTS = ("1.1", "2.1", "6.1")
SAMPLE_PER_GROUP = 10
SEED = 2023
ORTHOIMAGERY = re.compile(r"ορθοφωτ|ορθο/φ|αεροφωτ|δορυφορικ|orthophoto|aerial|\bortho|\bvlso\b|\buav\b|drone"
                          r"|μη επανδρωμεν")
ACT_SCAN_NAME = re.compile(r"fs\d{6}|rasrym")
RASTER = "_ras_"
LEGAL_ACT = re.compile(r"\bφεκ\b|διαγραμμ(?!\w*\s+αποτυπωσ)|τροποποιησ|ρυμοτομ|πραξ\w* (εφαρμογ|αναλογισμ)|κυρωσ|\bαποφασ"
                       r"|οριοθετησ\w* οικισμ|σχοοαπ|\bγπσ\b|\bτπσ\b|\bεπσ\b|\bentaxi|ενταξ\w* στο σχεδι|πινακιδ\w* [a-zα-ω]?\d"
                       r"|διορθωτικ|αδει\w* (δομησ|οικοδομ)")
LOCAL_ENVIRONMENT = re.compile(r"^(\w+ ){0,2}εκπομπ|\bκαδ(οι|ων|οσ)\b|αποκομ+ιδ|απορρι+μ+ατοφορ"
                               r"|δρομολογ\w* (\w+ )?(απορρι|ανακυκλ)|ζων\w* απορρι")
ENVIRONMENT = re.compile(r"εκπομπ|ρυπαν|θορυβ|αποβλητ|απορριμ|ανακυκλ|περιβαλλοντ|πρασιν|\bδασ|κλιματ|ενεργειακ"
                         r"|υγροτοπ|αιγιαλ|παραλι|ακτογρ|θαλασσ|υδατ|\bνερ|εδαφ|γεωθερμ|μεταλλευ|\bτοπι(ο|ου|α|ων)\b"
                         r"|πυρκαγι|βροχ|υγρασι|θερμοκρασι|\bανεμ|παγετ|καυσων|ξηρασι|humidex|δυσφορι"
                         r"|θερμ\w* (ημερ|νυχτ)|μελλοντικ\w* περιοδ|\bpr ?<|\d\s?[°ο]c\b|ακτινοβολ|ηλιοφανει"
                         r"|ε\.θ\.ε\.|επιφανειακ\w* θερμοκρασ")
# Terms of the map layers added to the patterns of the Annex items for this classification only; the patterns of
# criteria/hvd_annex_items.csv were written for the search of the whole catalogue (16_hvd_annex_coverage.py) and stay
# as judged there. Found in the most frequent words of the titles that the patterns alone left in the group neither.
LAYER_TERMS = {
    "1.1-01": r"^(ορι\w* )?(δημοτικ\w*[- ]τοπικ\w* κοινοτητ\w*|δημοτικ\w* (ενοτητ|κοινοτητ)\w*|τοπικ\w* κοινοτητ\w*"
              r"|περιφερει\w*|περιφερειακ\w* ενοτητ\w*)$|\bορι\w* (δημ(ου|ων)|περιφερει|δημοτικ\w* ενοτητ)",
    "1.1-03": r"αριθμησ\w* οδων",
    "1.1-05": r"κτηματογραφ|αναδασμ|κληροτεμαχ|διανομ\w* (υπουργειου γεωργιασ|συνοικισμ)",
    "2.1-T01": r"\bρεμα|υδρολογικ|υπολεκαν|υδροσυλλογ|υδατικ\w* συστημ|μεταβατικ\w* υδατ|παρακτι\w* υδατ",
    "2.1-T02": r"μνημει|αρχαιολογικ\w* (ζων|χωρ|τοπ)|ζων\w* (προστασι|αρχαιολογ)|ειδικ\w* προστασι"
               r"|ιστορικ\w* (τοπ|κεντρ)|κηρυγμεν|προστατευομεν\w* χωρ",
    "2.1-T03": r"pointcloud|point cloud|lidar",
    "2.1-T05": r"βλαστησ|ndvi|ndbi",
    "2.1-T09": r"αιολικ\w* εγκαταστ|\bα/γ\b",
    "2.1-T12": r"σχεδι\w* πολησ|εκτοσ σχεδιου|εντοσ σχεδιου|ορι\w* (του )?(εγκεκριμεν\w* )?σχεδιου|ορι\w* οικισμ"
               r"|οριογραμμ|συντελεστ\w* (αξιοποιησ|καλυψ|δομησ)|\bορ(οι|ων) δομησ|^μεγιστ\w* (υψοσ|καλυψη)$"
               r"|ποσοστ\w* καλυψ|αρτιοτητ|(μεταφορ|προσαυξησ|τομε)\w* συντελεστ"
               r"|κοινοχρηστ\w*\W+(κοιν[ωο]φελ\w*\W+)?χωρ|κοιν[ωο]φελ\w* χωρ|περιορισμ\w* δομησ|ιδιαιτερ\w* χρησ"
               r"|οικιστικ\w* περιοχ|(γενικ|αμιγ)\w* κατοικι|ευρει\w* ζων|οικισμ\w* (προ |κατω των)"
               r"|παραδοσιακ\w* οικισμ|σχεδι\w* (πε περιοχ|επεκτασ|πολεοδομικ\w* επεκτασ)",
    "2.1-T14": r"\(t ?= ?\d+\)|πλημμυ|συντελεστ\w* cn|εκτεθειμεν\w* σε κινδυν|(^|δασικ\w* )πυρκαγι"
               r"|χαρτ\w* πυρκαγι|κινδυν\w* (\w+ )?(πυρκαγι|εκδηλωσ)|καμεν\w* εκτασ|πυροπληκτ|\bfwi\b",
    "2.1-T16": r"υδροηλεκτρ|\bυ/η\b|\bμυηε\b|ηλιοθερμ|βιομαζ|βιοαερι|βιορευστ|\bσηθυα\b|συμπαραγωγ|υβριδικ\w* σταθμ"
               r"|\bφ/β\b|υδρογονου|μοναδ\w* αποθηκευσ|σφαγει|τυροκομει|οινοποιει|μοναδ\w* δευτερογεν|ελαιουργει"
               r"|ελαιοτριβει",
    "2.1-D07": r"heavy metal|hydrocarbon|pesticide|biocide|\bpah\b",
    "6.1-01": r"αρτηρι|πεζοδρομ|συλλεκτηρι|ποδηλατοδρομ|ποδηλατολωρ|ηπιασ κυκλοφορ|\bοδοι\b|δικτυ\w* (\w+ )?οδων",
}


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_table(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"File not found: {relative(path)}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalise(text: str) -> str:
    """Lower case without accents, with the final sigma written as a sigma, as in 16_hvd_annex_coverage.py."""
    decomposed = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").replace("ς", "σ")


def theme_patterns(items: list[dict]) -> list[tuple[str, re.Pattern]]:
    """The patterns of the datasets of the Annex whose content can be a map layer (points 1.1, 2.1 and 6.1), with the
    terms of the map layers of LAYER_TERMS."""
    themes = []
    for row in items:
        if row["annex_point"] not in THEME_POINTS:
            continue
        extra = LAYER_TERMS.get(row["item_id"])
        themes.append((row["item_id"], re.compile(row["patterns"] + (f"|{extra}" if extra else ""))))
    unknown = sorted(set(LAYER_TERMS) - {item_id for item_id, _ in themes})
    if unknown:
        raise SystemExit(f"Terms of map layers for items that are not in the list of the Annex: {', '.join(unknown)}")
    return themes


def classify(name: str, title: str, themes: list[tuple[str, re.Pattern]]) -> tuple[str, str]:
    """The group of a layer and the rule that placed it; the first rule that applies decides."""
    text = normalise(title).strip()
    if ORTHOIMAGERY.search(text):
        return BOTH, "orthoimagery"
    names_an_act = bool(LEGAL_ACT.search(text))
    if ACT_SCAN_NAME.search(name) or (names_an_act and (RASTER in name or MAP_VIEW_ONLY in name)):
        return BROAD, "scan of a legal act"
    if LOCAL_ENVIRONMENT.search(text):
        return BROAD, "emissions or waste collection"
    for item_id, pattern in themes:
        if pattern.search(text):
            return BOTH, f"theme {item_id}"
    if names_an_act:
        return BROAD, "legal act or plan"
    if ENVIRONMENT.search(text):
        return BROAD, "environmental term"
    return NEITHER, "none"


def harvested_layers(snapshot: Path, marked: dict[str, bool], themes: list[tuple[str, re.Pattern]]) -> list[dict]:
    """The datasets of the snapshot harvested from GIS servers, with their group."""
    layers = []
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            name = record.get("name") or ""
            if (record.get("type") or "dataset") != "dataset" or not name.startswith(HARVEST_PREFIX):
                continue
            organisation = record.get("organization") or {}
            group, rule = classify(name, record.get("title") or "", themes)
            layers.append({
                "name": name, "title": record.get("title") or "",
                "organisation": organisation.get("title", "") if isinstance(organisation, dict) else "",
                "address": f"{PORTAL}/dataset/{name}", "map_view_only": "yes" if MAP_VIEW_ONLY in name else "no",
                "marked_high_value": "yes" if marked.get(name) else "no", "group": group, "rule": rule,
            })
    return layers


def draw_sample(layers: list[dict]) -> list[dict]:
    """Ten layers of each group drawn at random with a fixed seed, so that the same snapshot gives the same sample."""
    generator = random.Random(SEED)
    sample = []
    for group in GROUPS:
        members = sorted((layer for layer in layers if layer["group"] == group), key=lambda layer: layer["name"])
        chosen = generator.sample(members, min(SAMPLE_PER_GROUP, len(members)))
        sample += sorted(chosen, key=lambda layer: layer["name"])
    return sample


def load_check(path: Path, sample: list[dict]) -> dict[str, dict]:
    """The group that the reviewer gave to each layer of the sample, if recorded; the run stops on a row that cannot be
    used."""
    if not path.exists():
        return {}
    names = {layer["name"] for layer in sample}
    check = {}
    for number, row in enumerate(read_table(path), start=2):
        place = f"{relative(path)}, line {number}"
        if row["name"] not in names:
            raise SystemExit(f"{place}: {row['name']} is not in the sample")
        if row["group_by_reviewer"] not in GROUPS:
            raise SystemExit(f"{place}: group '{row['group_by_reviewer']}' is not one of {', '.join(GROUPS)}")
        if row["name"] in check:
            raise SystemExit(f"{place}: second row for {row['name']}")
        check[row["name"]] = row
    missing = sorted(names - set(check))
    if missing:
        raise SystemExit(f"{relative(path)} has no row for {len(missing)} layers of the sample")
    return check


def agreement(sample: list[dict], check: dict[str, dict]) -> dict[str, tuple[int, int]]:
    """For each group of the rule: the layers on which the reviewer agrees, and the layers checked."""
    result = {}
    for group in GROUPS:
        members = [layer for layer in sample if layer["group"] == group]
        agreed = sum(check[layer["name"]]["group_by_reviewer"] == group for layer in members)
        result[group] = (agreed, len(members))
    return result


def share(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else ""


def md_cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def build_summary(date: str, layers: list[dict], catalogue_size: int, sample: list[dict], check: dict) -> str:
    groups = Counter(layer["group"] for layer in layers)
    lines = [
        f"# What the broad reading of point 2.1 would add to the high-value datasets, snapshot of {date}", "",
        f"The portal harvests {len(layers):,} map layers from the GIS servers of "
        f"{len({layer['organisation'] for layer in layers})} public bodies ({share(len(layers), catalogue_size)} of the "
        f"{catalogue_size:,} datasets); {sum(layer['map_view_only'] == 'yes' for layer in layers):,} of them only show a "
        f"map and {sum(layer['marked_high_value'] == 'yes' for layer in layers):,} carry a high-value marking. Point 2.1 of "
        "the Annex adds to the high-value datasets all the environmental information of Directive 2003/4/EC, which covers "
        "measures such as plans and legislation that affect land and landscape (Article 2(1)(c)); the narrow reading "
        "(DECISIONS.md #17) leaves this clause out and does not count scans of single legal acts. Every layer is placed in "
        "a group by rule, from its title and the name of its source; the rule is checked on a random sample.", "",
        "| Group | Layers | Share | Only a map view | Marked high-value |", "| --- | ---: | ---: | ---: | ---: |",
    ]
    for group in GROUPS:
        members = [layer for layer in layers if layer["group"] == group]
        lines.append(f"| {group} | {len(members):,} | {share(len(members), len(layers))} | "
                     f"{sum(layer['map_view_only'] == 'yes' for layer in members):,} | "
                     f"{sum(layer['marked_high_value'] == 'yes' for layer in members):,} |")
    rules = Counter((layer["group"], layer["rule"].split(" ")[0] if layer["rule"].startswith("theme") else layer["rule"])
                    for layer in layers)
    lines += ["", "| Group | Rule | Layers |", "| --- | --- | ---: |"]
    for (group, rule), count in sorted(rules.items(), key=lambda item: (GROUPS.index(item[0][0]), -item[1])):
        lines.append(f"| {group} | {rule} | {count:,} |")
    by_organisation: dict[str, Counter] = defaultdict(Counter)
    for layer in layers:
        by_organisation[layer["organisation"]][layer["group"]] += 1
    lines += ["", "| Body | Layers | " + " | ".join(GROUPS) + " |", "| --- | ---: | ---: | ---: | ---: |"]
    for organisation, count in sorted(by_organisation.items(), key=lambda item: -sum(item[1].values()))[:10]:
        lines.append(f"| {md_cell(organisation)} | {sum(count.values()):,} | "
                     + " | ".join(f"{count[group]:,}" for group in GROUPS) + " |")
    lines += ["", f"## Check of the rule on {len(sample)} layers drawn at random", ""]
    if check:
        agreed = agreement(sample, check)
        lines += ["Each layer of the sample was judged from its full metadata in the snapshot (title, description, tags "
                  "and resources) against the checklist of DECISIONS.md #62.", "",
                  "| Group of the rule | Layers checked | Agreed by the reviewer |", "| --- | ---: | ---: |"]
        for group in GROUPS:
            done, checked = agreed[group]
            lines.append(f"| {group} | {checked} | {done} |")
        total_done, total_checked = sum(v[0] for v in agreed.values()), sum(v[1] for v in agreed.values())
        borderline = sum(check[layer["name"]]["note"].startswith("Borderline") for layer in sample)
        lines += ["", f"Agreement over the sample: {total_done} of {total_checked}; {borderline} judgements are marked "
                  "as borderline in their note.", "",
                  "| Layer | Group of the rule | Group of the reviewer | Note |", "| --- | --- | --- | --- |"]
        for layer in sample:
            judged = check[layer["name"]]
            if judged["group_by_reviewer"] != layer["group"]:
                lines.append(f"| [{md_cell(layer['title'])}]({layer['address']}) | {layer['group']} | "
                             f"{judged['group_by_reviewer']} | {md_cell(judged['note'])} |")
    else:
        lines += ["The judgement of the reviewer is not recorded yet (`criteria/hvd_broad_reading_check.csv`)."]
    lines += ["", f"Narrow reading: the {groups[BOTH]:,} layers of the group both readings are high-value by their "
              f"content, without a marking in most cases. Broad reading: the {groups[BROAD]:,} layers of the group broad "
              "reading only would be added, most of them scans of single legal acts of town planning, so that "
              f"{groups[BOTH] + groups[BROAD]:,} map layers would be high-value instead of {groups[BOTH]:,}."]
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def newest_snapshot() -> Path:
    files = sorted(RAW_DIR.glob("catalog_????-??-??.jsonl.gz"))
    if not files:
        raise SystemExit("No catalogue snapshot in data/raw.")
    return files[-1]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="What the broad reading of point 2.1 of the Annex would add.")
    parser.add_argument("--snapshot", type=Path, default=None, help="catalogue snapshot (default: the newest in data/raw)")
    args = parser.parse_args()

    snapshot = args.snapshot or newest_snapshot()
    found = re.search(r"(\d{4}-\d{2}-\d{2})", snapshot.name)
    if not found:
        raise SystemExit(f"No date in the name of {relative(snapshot)}")
    date = found.group(1)
    metadata = read_table(PROCESSED_DIR / f"metadata_checks_{date}.csv")
    marked = {row["name"]: row["m9_marked"] == "True" for row in metadata}
    layers = harvested_layers(snapshot, marked, theme_patterns(read_table(ITEMS_FILE)))
    if not layers:
        raise SystemExit("No harvested map layer in the snapshot")
    sample = draw_sample(layers)
    check = load_check(CHECK_FILE, sample)

    out_dir = OUT_DIR / f"hvd_broad_reading_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    layers_file = PROCESSED_DIR / f"hvd_broad_reading_{date}.csv"
    sample_file = PROCESSED_DIR / f"hvd_broad_reading_sample_{date}.csv"
    write_csv(layers_file, [{key: value for key, value in layer.items() if key != "title"} for layer in layers])
    write_csv(sample_file, [dict(layer, group_by_reviewer=check.get(layer["name"], {}).get("group_by_reviewer", ""))
                            for layer in sample])
    (out_dir / "summary.md").write_text(build_summary(date, layers, len(metadata), sample, check), encoding="utf-8",
                                        newline="\n")

    groups = Counter(layer["group"] for layer in layers)
    print(f"Snapshot: {relative(snapshot)}")
    print(f"Harvested map layers: {len(layers):,}; " + ", ".join(f"{group} {groups[group]:,}" for group in GROUPS))
    if check:
        agreed = agreement(sample, check)
        print("Agreement of the rule: " + ", ".join(f"{group} {done} of {checked}" for group, (done, checked)
                                                     in agreed.items()))
    else:
        print(f"Sample for the check: {len(sample)} layers; judgement not recorded yet")
    print("Files:")
    for path in (layers_file, sample_file, out_dir / "summary.md"):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
