import re

VERSION = "1.3"
EDSM_API_URL = "https://www.edsm.net/api-v1/systems?systemName={}&showId=1"
EDSM_SYSTEM_URL = "https://www.edsm.net/en/system/id/{}/name/{}"
SPHERE_SYSTEMS_API_URL = "https://www.edsm.net/api-v1/sphere-systems?x={}&y={}&z={}&radius={}&showId=1&showCoordinates=1"
last_queried_system = None