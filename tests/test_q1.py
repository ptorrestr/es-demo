from typing import Optional
import requests
import logging
import pytest
import csv
import json
import pathlib
from dataclasses import dataclass
from dataclasses_json import dataclass_json

BUFFER_SIZE = 2500


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


@pytest.fixture(scope="module", autouse=True)
def populate_and_delete(elasticsearch_ready):
    # Create index
    index = "m-index-1"
    uri = f"{elasticsearch_ready}/{index}"
    settings = json.loads(pathlib.Path("./index.json").read_text())
    while True:
        resp = requests.put(uri, json=settings)
        if resp.status_code == 200:
            break
        elif resp.status_code == 400:
            requests.delete(uri)
        else:
            assert False, print(resp.text)
    # Populate index
    num_lines = sum(1 for line in open("productos_cleaned.csv")) - 1
    with open("productos_cleaned.csv", "r") as f:
        reader = csv.DictReader(f, delimiter=",", quotechar='"')
        bulk_msg = []
        for i, row in enumerate(reader):
            p = Product.from_dict({"id": i, **row})
            bulk_msg.append(json.dumps({"index": {"_index": index, "_id": i}}))
            bulk_msg.append(p.to_json())
            if (i + 1) % BUFFER_SIZE == 0 or i + 1 == num_lines:
                bulk_msg.append("")
                resp = requests.put(
                    f"{uri}/_bulk",
                    data="\n".join(bulk_msg),
                    headers={"content-type": "application/json"},
                ).raise_for_status()
                print(
                    "Data insterted {}/{} ({:.2f})".format(
                        i + 1, num_lines, (i + 1) / num_lines
                    )
                )

    yield uri


@pytest.mark.parametrize("query", sorted(pathlib.Path("./queries").glob("q1*.json")))
def test_multi_language(populate_and_delete, query, caplog):
    with caplog.at_level(logging.DEBUG):
        q = json.loads(pathlib.Path(query).read_text())
        resp = requests.get(f"{populate_and_delete}/_search", json=q)
        resp.raise_for_status()
        d = resp.json()
        assert len(d["hits"]["hits"]) > 0, print(resp.text)
        print()
        print(
            "Top results for query: '{}', terms: '{}'".format(
                query, q["query"]["multi_match"]["query"]
            )
        )
        print("\t".join(["id", "score", "description"]))
        for hit in d["hits"]["hits"]:
            print(
                "\t".join(
                    [hit["_id"], str(hit["_score"]), hit["_source"]["description"]]
                )
            )
