import random

class ETAService:
    @staticmethod
    def calculate_eta(incident_location: str, department_name: str) -> float:
        # Mock ETA calculation for hackathon
        # In a real app, this would use a mapping/routing API
        base_eta = random.uniform(2.0, 5.0)
        
        # Add some variation based on location name length (deterministic randomness)
        if incident_location:
            base_eta += len(incident_location) % 3
            
        return round(base_eta, 1)

    @staticmethod
    def replan_eta(current_eta: float) -> float:
        # Simulate traffic or route issues
        return round(current_eta + random.uniform(1.0, 3.0), 1)
