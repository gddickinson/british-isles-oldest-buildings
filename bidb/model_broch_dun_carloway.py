"""Builder of the Dun Carloway model (roadmap SH4c): see bidb.model_simple."""
from .model_simple import broch


def spec():
    return broch("dun_carloway")
