import requests
from core.constants import EDSM_API_URL

def check_system_on_edsm(system_name):
    try:
        response = requests.get(EDSM_API_URL.format(system_name))
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return True, data.get("id", None), response.status_code
        else:
            return False, None, response.status_code
    except Exception as e:
        print(f"Error querying EDSM: {e}")
        return None, None, None