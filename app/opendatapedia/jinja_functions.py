from jinja2 import Template
import json

import opendatapedia.config as c
import opendatapedia.globals as g

from opendatapedia.dataset  import DataSets, DataSet
from opendatapedia.utils    import pretty_url

html_colors = [
    'red', 
    'green', 
    'blue',
    'violet'
    'yellow',
    'purple',
    'orange',
    'pink',
    'gray'
    'fuchsia',
    'cyan',
    'brown',
    'olive',
    'maroon',
    'aqua',
    'teal',
    'aquamarine',
    'steelblue',
    'skyblue',
    'brown',
    'lime',
    'magenta',
    'lavender',
    'blueviolet'
    ]

color_set = {}

def define_jinja_functions(template):
    template.globals = {
        'chart_bar_horizontal': chart_bar_horizontal,
        'chart_doughnut': chart_doughnut,
        'chart_histogram': chart_histogram,
        'chart_pie': chart_pie,
        'dataset_field_label': dataset_field_label,
        'dataset_field_values_count': dataset_field_values_count,
        'dataset_nb_items': dataset_nb_items,
        'dataset_rows': dataset_rows,
        'datatable': datatable,
        'map': mapbox,
        'map_choropleth': map_choropleth,
        'zfill': zfill,
    }


def _row_filters_validate(row={}, match_all={}, match_any={}):
    matches_all = 0
    matches_any = 0
    for f in match_all:
        if row[f] == match_all[f]:
            matches_all += 1
    for f in match_any:
        if row[f] == match_any[f]:
            matches_any += 1
    if (len(match_any) == 0 or matches_any > 0) and (matches_all == len(match_all)):
        return True
    else:
        return False

def dataset_field_label(dataset_id: str, field_id: str):
    ds = DataSets().dataset(dataset_id)
    for f in ds.data_fields:
        if f['id'] == field_id:
            return f['label']
    return None 

def chart_histogram(dataset_id: str, chart_id="chart_histogram", y_label="", date_field=None, sets=[], **filters):
    g.trace_datasets_in_page(dataset_id)
    ds = DataSets().dataset(dataset_id)
    json_file = f"{c.PUBLIC_DATA_DIR}/{ds.data_file}"
    with open(json_file) as fh:
        content = json.load(fh)
        if hasattr(ds, 'data_root'):
            data_root = content[ds.data_root]
        else:
            data_root = content
        tmp_datasets = {}
        count = 0
        for row in data_root:
            filter_matches = 0
            for f in filters:
                if row[f] == filters[f]:
                    filter_matches += 1
            if filter_matches == len(filters):
                for i in sets:
                    if i not in tmp_datasets:
                        tmp_datasets[i] = { "data": [] }
                    tmp_datasets[i]['data'].append({"x": row[date_field], "y": row[i]})
        chart_datasets = []
        color_index = 0
        for k in tmp_datasets.keys():
            chart_datasets.append({
                "borderColor": html_colors[color_index], 
                "backgroundColor": html_colors[color_index],
                "label": dataset_field_label(dataset_id, k), 
                "data": tmp_datasets[k]['data'], 
                "fill": "false",
                "type": "line"
                })
            color_index += 1
    with open(f"{c.TEMPLATES_GENERIC_DIR}/chart_histogram.j2") as tpl_fh:
        template = Template(tpl_fh.read())
    return template.render(
            chart_id=chart_id,
            chart_datasets=chart_datasets,
            y_label=y_label)


def chart_bar_horizontal(dataset_id: str, chart_id="chart_bar_horizontal", chart_height=100, chart_width=600, title="", field="", match_all={}, match_any={}):
    g.trace_datasets_in_page(dataset_id)
    ds = DataSets().dataset(dataset_id)
    json_file = f"{c.PUBLIC_DATA_DIR}/{ds.data_file}"
    with open(json_file) as fh:
        content = json.load(fh)
        if hasattr(ds, 'data_root'):
            data_root = content[ds.data_root]
        else:
            data_root = content
        tmp_datasets = {}
        for row in data_root:
            if _row_filters_validate(row, match_all, match_any):
                if row[field] not in tmp_datasets:
                    tmp_datasets[row[field]] = 1
                else:
                    tmp_datasets[row[field]] = tmp_datasets[row[field]] + 1
        chart_datasets = []
        chart_datasets_labels = []
        color_index = 0
        for k in tmp_datasets.keys():
            color = None
            if k in color_set:
                color = color_set[k]
            else:
                color =  html_colors[color_index]
                color_set[k] = color
            chart_datasets.append({
                "borderColor": color, 
                "backgroundColor": color,
                "label": k, 
                "data": [ tmp_datasets[k] ], 
                })
            color_index += 1
    with open(f"{c.TEMPLATES_GENERIC_DIR}/chart_bar_horizontal.j2") as tpl_fh:
        template = Template(tpl_fh.read())
    return template.render(
            chart_id=chart_id,
            chart_datasets=chart_datasets,
            chart_datasets_labels=[field],
            chart_title=title,
            chart_height=chart_height, 
            chart_width=chart_width,
            )

def chart_doughnut(dataset_id: str, chart_id="chart_doughnut", 
        chart_title="", field="", chart_height=300, chart_width=400, match_all={}, match_any={}):
    return chart_doughnut_or_pie(dataset_id, chart_type='doughnut', chart_height=chart_height, chart_width=chart_width, 
        chart_id=chart_id, chart_title=chart_title, field=field, match_all=match_all, match_any=match_any)

def chart_pie(dataset_id: str, chart_id="chart_pie", 
        chart_title="", field="", chart_height=300, chart_width=400, match_all={}, match_any={}):
    return chart_doughnut_or_pie(dataset_id, chart_type='pie', chart_height=chart_height, chart_width=chart_width, 
        chart_id=chart_id, chart_title=chart_title, field=field, match_all=match_all, match_any=match_any)

def chart_doughnut_or_pie(dataset_id: str, chart_type='pie', chart_id="", 
        chart_title="", field="", chart_height=300, chart_width=400, match_all={}, match_any={}):
    g.trace_datasets_in_page(dataset_id)
    ds = DataSets().dataset(dataset_id)
    json_file = f"{c.PUBLIC_DATA_DIR}/{ds.data_file}"
    with open(json_file) as fh:
        content = json.load(fh)
        if hasattr(ds, 'data_root'):
            data_root = content[ds.data_root]
        else:
            data_root = content
        tmp_datasets = {}
        for row in data_root:
            if _row_filters_validate(row, match_all, match_any):
                if row[field] not in tmp_datasets:
                    tmp_datasets[row[field]] = 1
                else:
                    tmp_datasets[row[field]] = tmp_datasets[row[field]] + 1
        chart_datasets = []
        dataset_colors = []
        dataset_data = []
        dataset_labels = []
        color_index = 0
        for k in tmp_datasets.keys():
            color = None
            if k in color_set:
                color = color_set[k]
            else:
                color =  html_colors[color_index]
                color_set[k] = color
            dataset_colors.append(color)
            dataset_data.append(tmp_datasets[k])
            dataset_labels.append(k)
            color_index += 1
        chart_datasets.append({
            "backgroundColor": dataset_colors,
            "data": dataset_data,
            })
    with open(f"{c.TEMPLATES_GENERIC_DIR}/chart_doughnut_or_pie.j2") as tpl_fh:
        template = Template(tpl_fh.read())
    return template.render(
            chart_id=chart_id,
            chart_type=chart_type,
            chart_datasets=chart_datasets,
            chart_labels=dataset_labels,
            chart_title=chart_title,
            chart_height=chart_height,
            chart_width=chart_width
            )


def dataset_field_values_count(dataset_id: str, field, **filters):
    """
    """
    g.trace_datasets_in_page(dataset_id)
    ds = DataSets().dataset(dataset_id)
    json_file = f"{c.PUBLIC_DATA_DIR}/{ds.data_file}"
    count = {}
    with open(json_file) as f:
        data = json.load(f)
        for row in data['data']:
            filter_matches = 0
            for f in filters:
                if row[f] == filters[f]:
                    filter_matches += 1
            if filter_matches == len(filters):
                if count.get(row[field]):
                    count[row[field]] = count[row[field]] + 1
                else:
                    count[row[field]] = 1
    return count

def dataset_nb_items(dataset_id: str, **filters):
    """
    """
    g.trace_datasets_in_page(dataset_id)
    ds = DataSets().dataset(dataset_id)
    json_file = f"{c.PUBLIC_DATA_DIR}/{ds.data_file}"
    data_root = ds.data_root
    with open(json_file) as fh:
        data = json.load(fh)
        if filters:
            count = 0
            for row in data[data_root]:
                filter_matches = 0
                for f in filters:
                    if row[f] == filters[f]:
                        filter_matches += 1
                if filter_matches == len(filters):
                    count +=1
            return count
        else:
            return len(data[data_root])

def dataset_rows(dataset_id: str, match_all={}, match_any={}):
    g.trace_datasets_in_page(dataset_id)
    ds = DataSets().dataset(dataset_id)
    json_file = f"{c.PUBLIC_DATA_DIR}/{ds.data_file}"
    data_root = ds.data_root
    rows = []
    with open(json_file) as fh:
        data = json.load(fh)
        for row in data[data_root]:
            if _row_filters_validate(row, match_all, match_any):
                rows.append(row)
    return rows

def datatable(dataset_id: str, data_root="data", fields=[]):
    """
    """
    g.trace_datasets_in_page(dataset_id)
    ds = DataSets().dataset(dataset_id)
    datatable_fields = []
    if fields:
        for f in ds.data_fields:
            if f['id'] in fields:
                datatable_fields.append(f)
    else:
        datatable_fields = ds.data_fields
    with open(f"{c.TEMPLATES_GENERIC_DIR}/datatable.j2") as tpl_fh:
        template = Template(tpl_fh.read())
    return template.render(
                id=dataset_id,
                json_file=ds.data_file, 
                data_root=ds.data_root, 
                fields=datatable_fields
                )

def mapbox(dataset_id: str, **filters):
    """
    """
    ds = DataSets().dataset(dataset_id)
    g.trace_datasets_in_page(dataset_id)
    json_file = f"{c.PUBLIC_DATA_DIR}/{ds.data_file}"
    data_root = "features" #ds.data_root
    features = []
    lat_min, lat_max, long_min, long_max = None, None, None, None
    with open(json_file) as fh:
        data = json.load(fh)
        if filters:
            count = 0
            for row in data[data_root]:
                filter_matches = 0
                for f in filters:
                    if row["properties"][f] == filters[f]:
                        filter_matches += 1
                if filter_matches == len(filters):
                    features.append(row)
    with open(f"{c.TEMPLATES_GENERIC_DIR}/map.j2") as tpl_fh:
        template = Template(tpl_fh.read())

    return template.render(
                features=features
                ) 


def map_choropleth(map_id: str, dataset_id: str, field, chart_id="", match_all={}, match_any={}):
    g.trace_datasets_in_page(dataset_id)
    ds = DataSets().dataset(dataset_id)
    json_file = f"{c.PUBLIC_DATA_DIR}/{ds.data_file}"
    with open(json_file) as fh:
        content = json.load(fh)
        if hasattr(ds, 'data_root'):
            data_root = content[ds.data_root]
        else:
            data_root = content
        tmp_datasets = {}
        for row in data_root:
            if _row_filters_validate(row, match_all, match_any):
                if row[field] not in tmp_datasets:
                    tmp_datasets[row[field]] = 1
                else:
                    tmp_datasets[row[field]] = tmp_datasets[row[field]] + 1
    with open(f"{c.TEMPLATES_GENERIC_DIR}/map_choropleth.j2") as tpl_fh:
        template = Template(tpl_fh.read())
    return template.render(
        map_id=map_id,
        chart_id=chart_id,
        values=tmp_datasets
    ) 

def field_values_count(json_file, field):
    """
    """
    count = {}
    with open(json_file) as f:
        data = json.load(f)
        for row in data['data']:
            if count.get(row[field]):
                count[row[field]] = count[row[field]] + 1
            else:
                count[row[field]] = 1
    return count

def zfill(value, width):
    return value.zfill(width)