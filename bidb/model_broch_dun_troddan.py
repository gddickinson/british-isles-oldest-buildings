"""Builder of the Dun Troddan model (roadmap SH4c): see bidb.model_simple."""
from .model_simple import broch


def spec():
    return broch("dun_troddan")
