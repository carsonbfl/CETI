import requests
from core.constants import EDASTRO_API_URL

def check_system_on_edastro(system_name):
    try:
        url = EDASTRO_API_URL.format(system_name)
        response = requests.get(url)
        status = response.status_code

        if status == 200:
            data = response.json()
            if data and isinstance(data, dict) and data.get("name"):  # System exists
                return True, url, status
            else:
                return False, url, status
        else:
            return False, url, status

    except Exception as e:
        print(f"[EDASTRO] Error: {e}")
        return False, None, 0

