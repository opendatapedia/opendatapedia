from jinja2     import Environment, FileSystemLoader, Template
import json
from pathlib    import Path, PurePath
from typing     import List
import markdown
import yaml

import opendatapedia.config as c
import opendatapedia.globals as g

from opendatapedia.config           import logger
from opendatapedia.dataset          import DataSets, DataSet
from opendatapedia.jinja_functions  import define_jinja_functions
from opendatapedia.utils            import pretty_url

jinja_loader = FileSystemLoader(c.TEMPLATES_DIR)

def dataset_loop(dataset_id: str):
    """
    """
    g.trace_datasets_in_page(dataset_id)
    ds = DataSets().dataset(dataset_id)
    json_file = f"{c.PUBLIC_DATA_DIR}/{ds.data_file}"
    data_root = ds.data_root
    with open(json_file) as fh:
        data = json.load(fh)
        return data[data_root]


class Page:


    def __init__(self, id: str, page):
        self.id = id
        for key in page:
            setattr(self, key, page[key])


    def _render_page_content(self, data):
        with open(f"{c.TEMPLATES_DIR}/{self.template_file}") as tpl_fh:
            template = Environment(loader=jinja_loader).from_string(tpl_fh.read())
            define_jinja_functions(template)
            content = template.render(data)
        return markdown.markdown(content)


    def _render_page_datasets_used(self):
        if g.current_page in ['odp_about', 'odp_dataset', 'odp_datasets', 'odp_pages']:
            return "" 
        with open(f"{c.TEMPLATES_GENERIC_DIR}/datasets_used.md.j2") as tpl_fh:
            template = Environment(loader=jinja_loader).from_string(tpl_fh.read())
            content = template.render(datasets_used=g.datasets_in_page[g.current_page])
        return markdown.markdown(content)


    def _render_page_top(self, title: str):
        if hasattr(self, 'hide_menu'):
            hide_menu = self.hide_menu
        else:
            hide_menu = False
        fh_top = open(f"{c.TEMPLATES_GENERIC_DIR}/page_top.html.j2")
        tpl_top = Environment(loader=jinja_loader).from_string(fh_top.read())
        return tpl_top.render({"odp": {"page": {"title": title}, "hide_menu": hide_menu}})


    def _render_page_bottom(self):
        if hasattr(self, 'hide_menu'):
            hide_menu = self.hide_menu
        else:
            hide_menu = False
        fh_bottom = open(f"{c.TEMPLATES_GENERIC_DIR}/page_bottom.html")
        tpl_bottom = Environment(loader=jinja_loader).from_string(fh_bottom.read())
        return tpl_bottom.render({"odp": {"hide_menu": hide_menu}})


    def render(self):
        loop = getattr(self, 'dataset_loop', None)
        if loop:
            loop_items = dataset_loop(loop)
            for item in loop_items:
                dest_url = pretty_url(Template(self.dest_url).render(item))
                self.render_template(dest_url, item)
        else: 
            self.render_template(self.dest_url, {})


    def render_template(self, dest_url, data):
        g.current_page = self.id
        title = self.title
        logger.info(f"Rendering Page '{dest_url}' (from template '{self.template_file}'")
        page_content_html = self._render_page_content(data)        
        page_top_html = self._render_page_top(title)
        page_datasets_used_html = self._render_page_datasets_used()
        page_bottom_html = self._render_page_bottom()
            
        dest_path = f"{c.PUBLIC_DIR}/{dest_url}"
        dest_dir = PurePath(dest_path).parent
        Path(dest_dir).mkdir(parents=True, exist_ok=True)
        with open(dest_path, "w") as fh:
            page_size = fh.write(
                page_top_html + 
                page_content_html + 
                page_datasets_used_html + 
                page_bottom_html)
        if g.current_page not in ['odp_about', 'odp_dataset', 'odp_datasets', 'odp_pages']: 
            g.odp_pages.append({"title": Template(title).render(data), "path": dest_url, "datasets": g.datasets_in_page[g.current_page], "size": page_size})
    

class Pages:

    pages = []

    def __init__(self) -> List[Page]:
        fh = open(c.CONFIG_PAGES_FILE)
        pages_in_yaml = yaml.load(fh, Loader=yaml.FullLoader)['pages']
        for p_id in pages_in_yaml:
            self.pages.append(Page(p_id, pages_in_yaml[p_id]))
    
    def __iter__(self):
       ''' Returns the Iterator object '''
       return PagesIterator(self)


class PagesIterator:

   def __init__(self, pages):
       self._cl_pages = pages
       self._index = 0

   def __next__(self):
       if self._index < len(self._cl_pages.pages):
            result = self._cl_pages.pages[self._index]
            self._index +=1
            return result
       raise StopIteration


def PagesRendering():
    logger.info("Pages Rendering...")
    for p in Pages():
        p.render()

    fh = open(c.CONFIG_DATASETS_FILE)
    datasets_in_yaml = yaml.load(fh, Loader=yaml.FullLoader)['datasets']
    data = []
    for ds_id in datasets_in_yaml:
        row = datasets_in_yaml[ds_id]
        row['id'] = ds_id
        data.append(row)
    json_file = f"{c.PUBLIC_DATA_DIR}/odp_datasets.json"
    with open(json_file, "w", encoding='utf-8') as json_fh:
        out = json.dumps({ "data": data })
        json_fh.write(out)

    json_file = f"{c.PUBLIC_DATA_DIR}/odp_pages.json"
    with open(json_file, "w", encoding='utf-8') as json_fh:        
        out = json.dumps({ "data": g.odp_pages })
        json_fh.write(out)

    fh = open(c.CONFIG_ODP_PAGES_FILE)
    odp_pages_in_yaml = yaml.load(fh, Loader=yaml.FullLoader)['pages']
    for p_id in odp_pages_in_yaml:
        p = Page(p_id, odp_pages_in_yaml[p_id])
        p.render()
