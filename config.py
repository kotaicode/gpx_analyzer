import os

class Config:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    OVERPASS_URL = "http://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT = 30
    BUFFER_SIZE = 0.0005  # ~50 meters 
    # Mapping of surface types to suitability scores for road and gravel bikes
    SURFACE_SUITABILITY = {
        "asphalt": (1.0, 1.0),
        "concrete": (1.0, 1.0),
        "paving_stones": (0.8, 1.0),
        "sett": (0.6, 1.0),
        "cobblestone": (0.5, 1.0),
        "metal": (0.6, 0.8),
        "wood": (0.5, 0.8),
        "gravel": (0.0, 1.0),
        "fine_gravel": (0.0, 1.0),
        "dirt": (0.0, 1.0),
        "earth": (0.0, 1.0),
        "grass": (0.0, 0.8),
        "sand": (0.0, 0.6),
        "mud": (0.0, 0.5),
        "compacted": (0.4, 1.0),
        "clay": (0.0, 0.8),
        "snow": (0.0, 0.2),
        "ice": (0.0, 0.1)
    }