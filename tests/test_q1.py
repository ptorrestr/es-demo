from typing import Optional
import requests
import logging
import pytest
import csv
import json
import pathlib
from dataclasses import dataclass
from dataclasses_json import dataclass_json

BUFFER_SIZE=2500
index = json.loads(pathlib.Path("./index.json").read_text())

@dataclass_json
@dataclass
class Product:
    id: int
    description: str
    origin: Optional[str]
    section: Optional[str]
    family: Optional[str]
    brand: Optional[str]
    variety: Optional[str]
    format: Optional[str]
    group: Optional[str]
    internet_description: Optional[str]
    manufacturer: Optional[str]


@pytest.fixture(autouse=True)
def populate_and_delete(elasticsearch_ready):
    # Create index
    index = "my-index-000001"
    uri = f"{elasticsearch_ready}/{index}"
    logging.info(uri)
    resp = requests.put(uri, json=index)
    # Populate index
    num_lines = sum(1 for line in open('productos_cleaned.csv')) - 1
    with open("productos_cleaned.csv", "r") as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        bulk_msg = []
        for i, row in enumerate(reader):
            p = Product.from_dict({"id":i, **row})
            bulk_msg.append(json.dumps({"index": {"_index":index, "_id": i}}))
            bulk_msg.append(p.to_json())
            if (i+1) % BUFFER_SIZE == 0 or i+1 == (num_lines) :
                bulk_msg.append("")
                resp = requests.put(f"{uri}/_bulk", data='\n'.join(bulk_msg), headers={'content-type':'application/json'}).raise_for_status()
                print("Data insterted {}/{} ({:.2f})".format(i+1, num_lines, (i+1)/num_lines))

    yield uri
    # Delete index and any document
    requests.delete(uri)

def test_insert_data(populate_and_delete, caplog):
    with caplog.at_level(logging.DEBUG):
        print(populate_and_delete)
        assert True