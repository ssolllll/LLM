def process_get_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}

def process_create_item(item: dict):
    return {"message": "Item created successfully", "item": item}

def process_insert_db(file_path: str):
    extension = file_path.split(".")[-1]
    if extension =="pdf" :
        convert_pdf()
    elif extension == "xlsx":
        convert_xlsx()
    elif extension == "csv":
        convert_csv()
    elif extension == "hwp":
        convert_hwp()
    return table_name

def convert_pdf():
    return None

def convert_xlsx():
    return None

def convert_csv():
    return None

def convert_hwp():
    return None