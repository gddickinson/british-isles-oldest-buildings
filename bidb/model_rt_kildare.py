"""Builder of the Kildare round tower model (roadmap SH4c): see bidb.model_simple."""
from .model_simple import round_tower


def spec():
    return round_tower("kildare")
