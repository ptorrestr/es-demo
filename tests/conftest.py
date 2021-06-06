import pytest
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

@pytest.fixture(scope="session")
def elasticsearch_ready(session_scoped_container_getter) -> str:
    """Wait for ElasticSearch to become responsive"""
    if not session_scoped_container_getter:
        raise RuntimeError("Containers are not ready")
    service = session_scoped_container_getter.get("es01")
    network = service.network_info[0]
    api_url = f"http://{network.hostname}:{network.host_port}"
    request_session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    request_session.mount("http://", HTTPAdapter(max_retries=retries))
    assert request_session.get(api_url)
    return api_url