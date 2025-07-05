import requests
from core.constants import SPANSH_SYSTEM_URL


def check_system_on_spansh(system_address):
    url = SPANSH_SYSTEM_URL.format(system_address)
    try:
        response = requests.get(url)
        visited = False
        if response.status_code == 200 and "Page Not Found" not in response.text:
            visited = True
        return visited, url, response.status_code
    except:
        return False, url, 0
