#!/usr/bin/env python3
"""Gera index.html com mapa Folium usando GeoJSON locais (camadas/)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import folium

DATASETS: Sequence[Tuple[str, Path]] = (
    ("Setores", Path("camadas/setores.geojson")),
    ("DRM 2022", Path("camadas/drm2022.geojson")),
    ("PMRR 2017", Path("camadas/pmrr2017.geojson")),
    ("Vistorias", Path("camadas/vistorias.geojson")),
)

OUTPUT_HTML = Path("index.html")
POLYGON_OPACITY = 0.25
POINT_OPACITY = 0.7
POINT_RADIUS = 6


def main() -> None:
    payload = load_datasets()
    bounds = calculate_bounds(payload)

    folium_map = folium.Map(location=((bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2), zoom_start=12)
    folium_map.fit_bounds(((bounds[1], bounds[0]), (bounds[3], bounds[2])))

    palette = ["#1f78b4", "#33a02c", "#e31a1c", "#ff7f00"]

    for idx, (name, rel_path, feature_collection) in enumerate(payload):
        color = palette[idx % len(palette)]
        tooltip = build_popup(feature_collection)
        layer_group = folium.FeatureGroup(name=name, show=True)
        geojson = folium.GeoJson(
            data=str(rel_path),
            name=name,
            embed=False,
            style_function=_style_factory(color),
            highlight_function=lambda feat, c=color: {
                "color": c,
                "weight": 3,
                "fillColor": c,
                "fillOpacity": min(1.0, POLYGON_OPACITY + 0.15),
            },
            tooltip=tooltip,
            marker=folium.CircleMarker(radius=POINT_RADIUS, fill=True, fill_opacity=POINT_OPACITY),
        )
        geojson.add_to(layer_group)
        layer_group.add_to(folium_map)

    folium.LayerControl(collapsed=False).add_to(folium_map)
    folium_map.save(str(OUTPUT_HTML))
    print(f"[OK] Arquivo gerado em {OUTPUT_HTML.resolve()}")


def load_datasets() -> List[Tuple[str, Path, Dict]]:
    payload: List[Tuple[str, Path, Dict]] = []
    missing: List[Path] = []

    for _, path in DATASETS:
        if not path.exists():
            missing.append(path)
    if missing:
        missing_str = "\n - ".join(str(p) for p in missing)
        print(f"Arquivos ausentes:\n - {missing_str}", file=sys.stderr)
        sys.exit(1)

    for name, path in DATASETS:
        with path.open("r", encoding="utf-8") as handler:
            data = json.load(handler)
        payload.append((name, path, data))
    return payload


def calculate_bounds(payload: Sequence[Tuple[str, Path, Dict]]) -> Tuple[float, float, float, float]:
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    found = False

    for _, _, data in payload:
        for feature in data.get("features", []):
            geometry = feature.get("geometry")
            if not geometry:
                continue
            for x, y in _iterate_coords(geometry):
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
                found = True

    if not found:
        raise RuntimeError("Não foi possível determinar os limites do mapa.")

    return (minx, miny, maxx, maxy)


def build_popup(feature_collection: Dict) -> folium.GeoJsonPopup | None:
    fields = sorted(_collect_property_keys(feature_collection))
    if not fields:
        return None
    aliases = [f"{field}:" for field in fields]
    return folium.GeoJsonPopup(fields=fields, aliases=aliases, labels=True, localize=True)


def _collect_property_keys(feature_collection: Dict) -> Iterable[str]:
    keys = set()
    for feature in feature_collection.get("features", []):
        props = feature.get("properties") or {}
        keys.update(props.keys())
    return keys


def _iterate_coords(geometry: Dict):
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")

    if geom_type == "Point":
        yield _xy(coords)
    elif geom_type in {"MultiPoint", "LineString"}:
        for coord in coords or []:
            yield _xy(coord)
    elif geom_type == "MultiLineString":
        for line in coords or []:
            for coord in line or []:
                yield _xy(coord)
    elif geom_type == "Polygon":
        for ring in coords or []:
            for coord in ring or []:
                yield _xy(coord)
    elif geom_type == "MultiPolygon":
        for polygon in coords or []:
            for ring in polygon or []:
                for coord in ring or []:
                    yield _xy(coord)
    elif geom_type == "GeometryCollection":
        for geom in geometry.get("geometries", []):
            yield from _iterate_coords(geom)


def _xy(coord):
    if coord is None or len(coord) < 2:
        raise ValueError("Coordenada inválida")
    return float(coord[0]), float(coord[1])


def _style_factory(color: str):
    def style(feature: Dict) -> Dict:
        geom_type = ((feature or {}).get("geometry") or {}).get("type", "")
        is_point = geom_type in {"Point", "MultiPoint"}
        return {
            "color": color,
            "weight": 2,
            "fillColor": color,
            "fillOpacity": POINT_OPACITY if is_point else POLYGON_OPACITY,
        }

    return style


if __name__ == "__main__":
    main()
