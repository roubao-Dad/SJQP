"""Residential concept massing engine. Not a regulatory or daylight certification."""
import argparse
import json
import math
import random
from pathlib import Path
from shapely.geometry import Polygon, box, mapping

MODES = ['rows', 'staggered', 'mixed_height', 'towers']
OBJECTIVES = ['capacity', 'value', 'comfort']

def load(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    polygon = Polygon(data['boundary'])
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError('Invalid parcel geometry')
    if data['site_area_m2'] <= 0 or data['far_limit'] <= 0:
        raise ValueError('Invalid site area / FAR')
    return data

def generate(data, mode, objective, seed):
    rng = random.Random(seed)
    usable = Polygon(data['boundary']).buffer(-data['setback_m'], join_style=2)
    if usable.is_empty:
        return None
    products = data['products']
    if mode == 'towers':
        products = [p for p in products if p['type'] == 'tower']
    elif mode != 'mixed_height':
        products = [p for p in products if p['type'] == 'slab']
    if not products:
        return None
    target = data['site_area_m2'] * data['far_limit']
    spacing = data['screening_spacing_m']
    minx, miny, maxx, maxy = usable.bounds
    y = miny + rng.uniform(0, 8)
    buildings = []
    row = 0
    counted = 0
    while y < maxy and len(buildings) < data.get('max_buildings', 60):
        x = minx + rng.uniform(0, 5) + ((row % 2) * 9 if mode == 'staggered' else 0)
        row_height = 0
        while x < maxx and len(buildings) < data.get('max_buildings', 60):
            p = products[(row + len(buildings)) % len(products)] if mode == 'mixed_height' else rng.choice(products)
            w, h = p['width_m'], p['depth_m']
            floors = min(p['floors'], math.floor(data['height_limit_m'] / p['floor_height_m']))
            if floors < 1:
                break
            geom = box(x, y, x + w, y + h)
            if usable.covers(geom) and all(geom.distance(b['_polygon']) + 1e-9 >= spacing for b in buildings):
                area = w * h * floors * p.get('counted_area_factor', 1)
                if counted + area <= target * 1.001:
                    buildings.append({
                        'id': len(buildings) + 1, 'product': p['name'], 'type': p['type'],
                        'floors': floors, 'height_m': round(floors * p['floor_height_m'], 2),
                        'counted_area_m2': round(area, 2), 'geometry': mapping(geom),
                        '_polygon': geom, '_value_factor': p.get('value_factor', 1),
                    })
                    counted += area
                    row_height = max(row_height, h)
            x += w + spacing + rng.uniform(0, 5)
        y += max(row_height, 12) + spacing + rng.uniform(0, 5)
        row += 1
    if not buildings:
        return None
    n = len(buildings)
    value = sum(b['counted_area_m2'] * b['_value_factor'] for b in buildings)
    comfortable_pairs = sum(
        1 for i, a in enumerate(buildings) for b in buildings[i+1:]
        if a['_polygon'].distance(b['_polygon']) >= spacing * 1.5
    )
    comfort = comfortable_pairs / max(1, n * (n-1) / 2)
    utilization = counted / target
    relative_value = value / (target * max(p.get('value_factor', 1) for p in products))
    weights = {
        'capacity': (0.8, 0.1, 0.1), 'value': (0.25, 0.65, 0.1),
        'comfort': (0.25, 0.15, 0.6),
    }[objective]
    score = sum(a*b for a, b in zip(weights, (utilization, relative_value, comfort)))
    for b in buildings:
        del b['_polygon']
        del b['_value_factor']
    return {
        'mode': mode, 'objective': objective, 'seed': seed, 'buildings': buildings,
        'metrics': {
            'building_count': n, 'counted_area_m2': round(counted, 2),
            'achieved_far': round(counted / data['site_area_m2'], 4),
            'far_target_ratio': round(utilization, 4),
            'relative_value_index': round(relative_value, 4),
            'spacing_comfort_proxy': round(comfort, 4), 'score': round(score, 5),
        },
        'checks': {
            'boundary_setback': 'pass', 'height_limit': 'pass',
            'simplified_spacing': 'pass', 'far_limit': 'pass',
            'daylight': 'NOT_EVALUATED', 'fire_access': 'NOT_EVALUATED',
            'parking': 'NOT_EVALUATED', 'local_code': 'NOT_EVALUATED',
        },
    }

def run(data, iterations):
    if iterations < 1:
        raise ValueError('iterations must be positive')
    result = []
    for mode in MODES:
        for objective in OBJECTIVES:
            candidates = [generate(data, mode, objective, seed) for seed in range(iterations)]
            candidates = [candidate for candidate in candidates if candidate is not None]
            if candidates:
                result.append(max(candidates, key=lambda candidate: candidate['metrics']['score']))
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--iterations', type=int, default=40)
    parser.add_argument('--output', default='results.json')
    args = parser.parse_args()
    data = load(args.config)
    schemes = run(data, args.iterations)
    payload = {
        'site': data['name'],
        'disclaimer': 'Concept geometry only. No statutory daylight or code compliance verified.',
        'schemes': schemes,
    }
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Generated', len(schemes), 'schemes; output:', args.output)
    for scheme in schemes:
        print(scheme['mode'], scheme['objective'],
              scheme['metrics']['achieved_far'], scheme['metrics']['building_count'])

if __name__ == '__main__':
    main()
