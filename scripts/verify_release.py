#!/usr/bin/env python3
"""Read-only release checks. No Docker, network or scientific rerun required."""
import ast
import csv
import json
import math
import re
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text())


def read_csv(path):
    with (ROOT / path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def near(actual, expected, tolerance=1e-5):
    if not math.isfinite(actual) or abs(actual - expected) > tolerance:
        raise AssertionError(f'Numeric mismatch: {actual} versus {expected}')


def slope(x, y):
    xm, ym = statistics.mean(x), statistics.mean(y)
    return sum((a-xm)*(b-ym) for a,b in zip(x,y)) / sum((a-xm)**2 for a in x)


def main():
    files = [p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts]
    pyfiles = [p for p in files if p.suffix == '.py']
    for p in pyfiles:
        ast.parse(p.read_text(), filename=str(p))
    for p in files:
        if p.suffix == '.json':
            json.loads(p.read_text())
        elif p.suffix == '.csv':
            with p.open(newline='') as stream:
                records = list(csv.reader(stream))
            assert records and all(len(row) == len(records[0]) for row in records), p

    g = read_json('external_validation/gnss_los_results.json')
    era = read_json('mintpy_redundant_era5/audit/audit_results.json')
    closure = read_json('mintpy_redundant/audit/closure_results.json')
    chain = read_json('mintpy/audit/audit_results.json')
    rows = read_csv('external_validation/gnss_los_comparison.csv')
    primary = {r['case']:r for r in rows if int(r['patch_size_px']) == 9}
    assert len(primary) == 4

    # Reproject included cleaned ENU records, using source viewing coefficients.
    cleaned = {s:{r['date']:r for r in read_csv(f'external_validation/gnss_processed/{s}_2024_cleaned.csv')}
               for s in ['ICMX','MMX1']}
    dates, contrasts = [], []
    for match in g['matching']['details']:
        dates.append(datetime.strptime(match['sentinel'], '%Y%m%d'))
        los = {}
        for s in cleaned:
            row = cleaned[s][match[s]]
            geometry = g['geometry']['stations'][s]
            los[s] = sum(float(row[c+'_m'])*geometry[k] for c,k in
                         [('east','los_e'),('north','los_n'),('up','los_u')])
        contrasts.append((los['ICMX'] - los['MMX1'])*1000)
    years = [(d-dates[0]).days/365.25 for d in dates]
    gnss = slope(years, contrasts)
    near(gnss, g['gnss_differential']['rate_mm_yr'])
    assert len(dates) == 10 and (dates[-1]-dates[0]).days == 168
    assert sum(m['ICMX_offset']==m['MMX1_offset']==0 for m in g['matching']['details']) == 6
    for actual, recorded in zip(contrasts, g['gnss_differential']['series_mm']):
        near(actual, recorded, 1e-4)

    comparisons = {}
    for name, decision in g['decision'].items():
        row = primary[name]
        difference = gnss - float(row['insar_diff_common_mm_yr'])
        near(difference, decision['gnss_minus_insar_mm_yr'])
        sys_terms = ['sys_cadence','sys_outlier','sys_matching','sys_patch']
        combined = math.sqrt(decision['stat_halfwidth_ar1']**2 + sum(decision[k]**2 for k in sys_terms))
        near(combined, decision['U95'])
        near(difference, float(row['gnss_minus_insar_mm_yr']))
        comparisons[name] = {'insar_mm_yr':float(row['insar_diff_common_mm_yr']),
                             'difference_mm_yr':difference,'U95':combined}

    # Reconstruct the reported graph, not the unavailable HDF5 stack.
    acquisitions = chain['dates']
    assert len(acquisitions) == 25 and acquisitions == sorted(set(acquisitions))
    edges = {tuple(sorted(pair)) for pair in zip(acquisitions[:-1], acquisitions[1:])}
    triangle_edges = set()
    for triangle in closure['triangles']:
        for key in ['edge_ab','edge_bc','edge_ac']:
            pair=tuple(sorted(triangle[key].split('_')))
            edges.add(pair);triangle_edges.add(pair)
    assert len(edges) == 31 and len(closure['triangles']) == 7
    bridges=[]
    for removed in sorted(edges):
        seen={acquisitions[0]}; todo=list(seen)
        while todo:
            u=todo.pop()
            for a,b in edges-{removed}:
                v=b if a==u else a if b==u else None
                if v is not None and v not in seen:
                    seen.add(v);todo.append(v)
        if len(seen)<25:bridges.append('_'.join(removed))
    assert len(bridges) == 10
    for mid in [('20240512','20240629'),('20240629','20240804')]:
        assert mid in triangle_edges and '_'.join(mid) not in bridges
    assert closure['mintpy_nonzero_pixels']==2334 and closure['mintpy_valid_pixels']==81299
    near(100*2334/81299, closure['mintpy_nonzero_pct'])

    stats=era['cases']; ca=stats['A_baseline_no_ramp']; cb=stats['B_baseline_linear_ramp']
    median_difference=cb['median_mm_yr']-ca['median_mm_yr']
    delta_median=era['comparisons']['ramp_effect_baseline_mm_yr']['median']
    for row in read_csv('mintpy_redundant_era5/audit/case_statistics.csv'):
        for key,value in row.items():
            if key != 'case':near(float(value),stats[row['case']][key])

    # Validate local links in the release-facing documentation.
    docs=[ROOT/'README.md',*sorted((ROOT/'docs').glob('*.md'))]
    links=0
    for doc in docs:
        for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if '://' in target or target.startswith('#'):continue
            path=target.split('#')[0]
            assert (doc.parent/path).exists(), f'Broken link in {doc.relative_to(ROOT)}: {target}'
            links+=1
    required_figures=[
        'mintpy_redundant/audit/closure_failures_by_triangle.png',
        'mintpy_redundant_era5/audit/fig_four_case_velocity_comparison.png',
        'mintpy_redundant/audit/fig_reference_sensitivity.png',
        'external_validation/fig_gnss_los_timeseries.png',
        'external_validation/fig_gnss_vs_insar_differential.png',
        'external_validation/fig_patch_sensitivity.png',
        'final_report/fig_station_locations.png',
        'mintpy_redundant_era5/audit/fig_gradient_comparison.png',
    ]
    assert all((ROOT/p).is_file() for p in required_figures)
    forbidden={'.cdsapirc','.netrc','.env','credentials.json','token.json'}
    assert not [p for p in files if p.name in forbidden or p.suffix in {'.h5','.zip','.grib','.tif','.pem','.key'}]
    assert max(p.stat().st_size for p in files)<50*1024*1024
    token_patterns=[r'ghp_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{40,}',
                    r'AKIA[A-Z0-9]{16}',r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',
                    r'(?i)(?:api[_-]?key|password|access_token)\s*[:=]\s*[\"\x27]?[A-Za-z0-9_/-]{24,}']
    hits=[]
    for p in files:
        if p.suffix in {'.png','.pdf'}:continue
        try:text=p.read_text()
        except UnicodeDecodeError:continue
        if any(re.search(pattern,text) for pattern in token_patterns):hits.append(str(p.relative_to(ROOT)))
    assert not hits, f'Potential credential pattern in: {hits}'
    print(json.dumps({'status':'passed','scientific_inversion_rerun':False,
        'gnss_rate_recomputed_from_cleaned_csv_mm_yr':gnss,'matched_epochs':len(dates),
        'comparisons':comparisons,'reported_graph_nodes':25,'reported_graph_edges':31,
        'cycle_rank':7,'bridges':bridges,'median_pixelwise_B_minus_A_mm_yr':delta_median,
        'difference_of_map_medians_B_minus_A_mm_yr':median_difference,
        'python_files_parsed':len(pyfiles),'local_document_links_checked':links,
        'indexed_figures_present':len(required_figures),'credential_pattern_hits':len(hits),
        'largest_file_bytes':max(p.stat().st_size for p in files)},indent=2))


if __name__ == '__main__':
    main()
