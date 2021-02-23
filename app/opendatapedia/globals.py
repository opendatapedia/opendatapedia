
odp_pages = []

current_page = None

datasets_in_page = {}

def trace_datasets_in_page(dataset_id: str):
    if current_page in datasets_in_page:
        datasets_in_page[current_page].append(dataset_id)
    else:
        datasets_in_page[current_page] = [dataset_id]