"""Make the bundled India state map and the state centroid table from DataMeet's state boundaries. Run on a
connected machine; the outputs are committed and served locally (no map tiles, no CDN, no lookup at run time).

    pip install pyshp==2.3.1            # this script only; not a SETHU dependency
    python scripts/make_india_map.py <folder with Admin2.shp/.shx/.dbf>

Source: https://github.com/datameet/maps, States/Admin2.* at commit 2c0c306a0c786a83876065a62b7b82646d8a639d
("Updated Ladhak & J&K boundry as per latest SOI Map", 2021). Licence: CC BY 4.0 (the repository's data licence),
attribution "India state boundaries by DataMeet India community". See docs/AI-PIPELINE.md, "A4, the India map".

What this script does to the boundaries, and nothing else: coordinates are rounded to 3 decimal places (about 110 m,
below one screen pixel at any zoom the map offers) and a point equal to the one before it is dropped. No line is
drawn, moved or simplified. A person must still check the result against Survey of India's official depiction
before any public use (docs/SECURITY.md, row 53).

Outputs:
  web/public/maps/india-states.json         GeoJSON FeatureCollection, property `name` (the source's ST_NM)
  backend/app/ai/data/state_centroids.json  {state: [latitude, longitude]}: the area-weighted centroid of each
                                            state's polygons, for early-warning clustering
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECIMALS = 3          # about 110 m: below one screen pixel at the closest zoom the map offers (a state)
SOURCE = {"dataset": "DataMeet India community, maps repository, States/Admin2",
          "url": "https://github.com/datameet/maps/tree/2c0c306a0c786a83876065a62b7b82646d8a639d/States",
          "commit": "2c0c306a0c786a83876065a62b7b82646d8a639d", "licence": "CC BY 4.0",
          "attribution": "India state boundaries by DataMeet India community (CC BY 4.0)",
          "note": "Boundaries as published, J&K and Ladakh updated per the Survey of India map (2021). Coordinates "
                  "rounded to 3 decimals; nothing simplified. Verify against Survey of India before public use."}


def ring(points, decimals=DECIMALS):
    """The ring rounded to `decimals`; a ring too small for that grid (a tiny islet) keeps 6 decimals instead, so
    no feature of the source is lost."""
    out = []
    for x, y in points:
        p = [round(x, decimals), round(y, decimals)]
        if not out or p != out[-1]:
            out.append(p)
    if out[0] != out[-1]:
        out.append(out[0])
    if len(out) >= 4:
        return out
    return ring(points, 6) if decimals < 6 else None


def area_centroid(rings):
    """Area-weighted centroid (planar, in degrees: fine for a state-sized polygon) and area of outer rings."""
    total = cx = cy = 0.0
    for r in rings:
        a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(r, r[1:], strict=False)) / 2
        if a == 0:
            continue
        cx += sum((x0 + x1) * (x0 * y1 - x1 * y0) for (x0, y0), (x1, y1) in zip(r, r[1:], strict=False)) / 6
        cy += sum((y0 + y1) * (x0 * y1 - x1 * y0) for (x0, y0), (x1, y1) in zip(r, r[1:], strict=False)) / 6
        total += a
    return (cy / total, cx / total) if total else None


def main(folder: str) -> None:
    import shapefile  # pyshp

    reader = shapefile.Reader(str(Path(folder) / "Admin2"))
    name_field = next(f[0] for f in reader.fields[1:] if f[0].upper() == "ST_NM")
    features, centroids, points, dropped = [], {}, 0, 0
    for shape_record in reader.iterShapeRecords():
        name = str(shape_record.record[name_field]).strip()
        shape = shape_record.shape
        parts = list(shape.parts) + [len(shape.points)]
        raw = [ring(shape.points[a:b]) for a, b in zip(parts, parts[1:], strict=False)]
        rings = [r for r in raw if r]
        dropped += len(raw) - len(rings)   # degenerate rings in the source itself (reported; expected 0)
        points += sum(len(r) for r in rings)
        # Shapefile rings: outer rings clockwise, holes counter-clockwise. GeoJSON polygons: [outer, *holes].
        polygons: list[list] = []
        for r in rings:
            signed = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(r, r[1:], strict=False))
            if signed <= 0 or not polygons:
                polygons.append([r])
            else:
                polygons[-1].append(r)
        features.append({"type": "Feature", "properties": {"name": name},
                         "geometry": {"type": "MultiPolygon", "coordinates": polygons}})
        outer = [p[0] for p in polygons]
        centroids[name] = [round(c, 4) for c in area_centroid(outer)]
    geo = {"type": "FeatureCollection", "source": SOURCE, "features": features}
    out = ROOT / "web/public/maps/india-states.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(geo, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    cent = ROOT / "backend/app/ai/data/state_centroids.json"
    cent.write_text(json.dumps({"source": SOURCE, "centroids": dict(sorted(centroids.items()))}, indent=1,
                               ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(features)} states and UTs, {points} points, {dropped} degenerate rings dropped, "
          f"{out.stat().st_size / 1e6:.1f} MB, sha256 "
          f"{hashlib.sha256(out.read_bytes()).hexdigest()}")
    print(sorted(centroids))


if __name__ == "__main__":
    main(sys.argv[1])
