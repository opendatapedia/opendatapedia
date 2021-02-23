import csv
import json
import os
from pathlib        import Path
import requests
from typing         import List
import yaml
from zipfile        import ZipFile

import opendatapedia.config as c
from opendatapedia.config   import logger
from opendatapedia.utils    import save_url_to_directory

import sys
from io import StringIO
import contextlib

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


class DataSet:

    def __init__(self, id: str, dataset=None):
        self.id = id
        if dataset is None:
            fh = open(c.CONFIG_DATASETS_FILE)
            datasets = yaml.load(fh, Loader=yaml.FullLoader)['datasets']
            for ds in datasets:
                if ds == id:
                    for key in datasets[ds]:
                        setattr(self, key, datasets[ds][key])
        else:
            for key in dataset:
                setattr(self, key, dataset[key])


    def fields_ids(self):
        ids = []
        for f in self.data_fields:
            src_id = f['src_id'] if 'src_id' in f else f['id']
            if 'code' not in f:
                ids.append({ 'id': f['id'], 'src_id': src_id })
        return ids

    def fields_labels(self):
        return [ f['label'] for f in self.data_fields ]

    def field_values_count(self, field):
        """
        """
        count = {}
        json_file = f"/public/data/{self.data_file}"
        data_root = self.data_root
        with open(json_file) as f:
            data = json.load(f)
            for row in data[data_root]:
                if count.get(row[field]):
                    count[row[field]] = count[row[field]] + 1
                else:
                    count[row[field]] = 1
        return count

    # def nb_items(self):
    #     data_file = self.data_file
    #     data_root = self.data_root
    #     with open(f"{c.DATA_DIR}/{data_file}") as f:
    #         data = json.load(f)

    def data_download(self, force=False):
        if not hasattr(self, 'download_url'):
            logger.warning(f"DataSet '{self.id}' has no 'download_url'")
            return
        url = self.download_url
        if hasattr(self, 'downloaded_file'):
            path = save_url_to_directory(url, c.PUBLIC_DATA_DIR, self.downloaded_file)
        else:
            path = save_url_to_directory(url, c.PUBLIC_DATA_DIR)
        file_ext = os.path.splitext(path)[1]
        if file_ext == '.zip':
            logger.info(f"Extracting '{self.file_from_zip}' from zip file '{path}'")
            ZipFile(path, 'r').extract(self.file_from_zip, path=c.DATA_DIR)
            path =  f"{c.DATA_DIR}/{self.file_from_zip}"

        file_ext = os.path.splitext(path)[1]
        if file_ext == '.csv':
            self.csv_to_json(path)

    def csv_to_json(self, path):
        Path(c.PUBLIC_DATA_DIR).mkdir(parents=True, exist_ok=True)
        json_file = f"{c.PUBLIC_DATA_DIR}/{self.data_file}"
        delimiter = self.csv_delimiter
        encoding = self.encoding if hasattr(self, 'encoding') else 'utf-8'
        logger.info(f"Generating '{json_file}' from csv file '{path}'...")
        with open(path, mode="r", encoding=encoding) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            with open(json_file, "w", encoding='utf-8') as jsonfile:
                data_rows = []
                fields_ids = self.fields_ids()
                for r_row in reader:
                    row = { f['id']: r_row[f['src_id']] for f in fields_ids }
                    for f in self.data_fields:
                        if 'code' in f:
                            with stdoutIO() as s:
                                exec(f['code'])
                                row[f['id']] = s.getvalue()
                    data_rows.append(row)
                json.dump({ "data": data_rows }, jsonfile, ensure_ascii=False)


class DataSets:

    datasets = []

    def __init__(self) -> List[DataSet]:
        fh = open(c.CONFIG_DATASETS_FILE)
        datasets_in_yaml = yaml.load(fh, Loader=yaml.FullLoader)['datasets']
        for ds_id in datasets_in_yaml:
            self.datasets.append(DataSet(ds_id, datasets_in_yaml[ds_id]))
        fh = open(c.CONFIG_ODP_DATASETS_FILE)
        odp_datasets_in_yaml = yaml.load(fh, Loader=yaml.FullLoader)['datasets']
        for ds_id in odp_datasets_in_yaml:
            self.datasets.append(DataSet(ds_id, odp_datasets_in_yaml[ds_id]))

    def dataset(self, dataset_id: str) -> DataSet:
        for ds in self.datasets:
            if ds.id == dataset_id: 
                return ds
        return None

    def __iter__(self):
       ''' Returns the Iterator object '''
       return DataSetsIterator(self)


class DataSetsIterator:
    ''' Iterator class '''
    def __init__(self, datasets_class):
        self._cl_ds = datasets_class
        self._index = 0

    def __next__(self):
       ''' Returns the next value from team object's lists '''
       if self._index < len(self._cl_ds.datasets):
            result = self._cl_ds.datasets[self._index]
            self._index +=1
            return result
       raise StopIteration


def DataSetsBuilding():
    logger.info("DataSets Building...")
    for ds in DataSets():
        ds.data_download()
