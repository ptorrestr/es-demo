from datetime import datetime, timedelta
import requests
import logging
import pytest
import json
import pathlib
from faker.factory import Factory
from dataclasses import dataclass
from dataclasses_json import dataclass_json

BUFFER_SIZE = 2500


@dataclass_json
@dataclass
class Query:
    id: int
    timestamp: int
    terms: str  # asume here we have the query terms


@pytest.fixture(scope="module", autouse=True)
def populate_and_delete(elasticsearch_ready):
    # Create index that contains multiple mappings
    index = "m-index-2"
    uri = f"{elasticsearch_ready}/{index}"
    settings = json.loads(pathlib.Path("./index2.json").read_text())
    while True:
        resp = requests.put(uri, json=settings)
        if resp.status_code == 200:
            break
        elif resp.status_code == 400:
            requests.delete(uri)
        else:
            assert False, print(resp.text)
    # Populate index with data. Here we assume the data contains fields for different
    # languages
    Faker = Factory.create
    fake = Faker()
    fake.seed(0)
    number_of_items = 10000
    bulk_msg = []
    print("Inserting fake queries")
    now = datetime.now()
    for i in range(number_of_items):
        p = Query.from_dict(
            {
                "id": i,
                "timestamp": int((now + timedelta(seconds=-i)).timestamp() * 1000),
                "terms": fake.last_name(),
            }
        )
        bulk_msg.append(json.dumps({"index": {"_index": index, "_id": i}}))
        bulk_msg.append(p.to_json())
        if (i + 1) % BUFFER_SIZE == 0 or i + 1 == number_of_items:
            bulk_msg.append("")
            resp = requests.put(
                f"{uri}/_bulk",
                data="\n".join(bulk_msg),
                headers={"content-type": "application/json"},
            ).raise_for_status()
            print(
                "Data insterted {}/{} ({:.2f})".format(
                    i + 1, number_of_items, (i + 1) / number_of_items
                )
            )
    # return index uri
    yield uri


def test_create_dashboard(populate_and_delete, caplog):
    """Create dashboard for kibana"""
    with caplog.at_level(logging.DEBUG):

        dashboard = json.loads(pathlib.Path("./dashboard.json").read_text())
        resp = requests.post(
            "http://localhost:5601/api/kibana/dashboards/import",
            headers={"kbn-xsrf": "true"},
            json=dashboard,
        )
        assert resp.status_code == 200, print(resp.text)
