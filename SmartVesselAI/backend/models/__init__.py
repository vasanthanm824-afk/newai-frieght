try:
    from backend.models.db_models import FreightRate, Vessel, Port, Cargo, Telemetry
except ModuleNotFoundError:
    from .db_models import FreightRate, Vessel, Port, Cargo, Telemetry
