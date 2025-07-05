import re

VERSION = "1.4"

EDASTRO_API_URL = "https://edastro.com/api/starsystem?q={}"
EDSM_API_URL = "https://www.edsm.net/api-v1/systems?systemName={}&showId=1"
EDSM_SYSTEM_URL = "https://www.edsm.net/en/system?systemName={}"
SPHERE_SYSTEMS_API_URL = "https://www.edsm.net/api-v1/sphere-systems?x={}&y={}&z={}&radius={}&showId=1&showCoordinates=1"
SPANSH_SYSTEM_URL = "https://spansh.co.uk/system/{}"

last_queried_system = None
