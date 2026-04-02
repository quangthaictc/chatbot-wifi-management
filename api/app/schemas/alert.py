from pydantic import BaseModel


class Alert(BaseModel):
    attack_type: str
    severity: str  # "CRITICAL" or "WARNING"
    dpid: int
    attacker_mac: str
    details: str
