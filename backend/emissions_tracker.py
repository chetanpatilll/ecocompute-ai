from datetime import datetime
from typing import Dict

import os
import json

try:
    # Optional dependency: full functionality when installed
    from codecarbon import OfflineEmissionsTracker, EmissionsTracker
    _CODECARBON_AVAILABLE = True
except ImportError:
    # Graceful fallback: minimal dummy tracker so the app still runs
    _CODECARBON_AVAILABLE = False

    class _DummyTracker:
        def __init__(self, *args, **kwargs):
            self._started = False

        def start(self):
            self._started = True

        def stop(self):
            # Return 0 emissions when CodeCarbon is unavailable
            return 0.0

    # Use dummy implementations so rest of the code can stay the same
    OfflineEmissionsTracker = _DummyTracker  # type: ignore
    EmissionsTracker = _DummyTracker  # type: ignore

import pandas as pd

class GPUEmissionsTracker:
    """Track GPU job emissions using CodeCarbon."""
    
    def __init__(self, country_code: str = "IN", output_dir: str = "data"):
        self.country_code = country_code
        self.output_dir = output_dir
        self.tracker = None
        self.emissions_log = []
        self.load_emissions_log()
    
    def load_emissions_log(self):
        """Load existing emissions data."""
        log_file = os.path.join(self.output_dir, "emissions.json")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                self.emissions_log = json.load(f)
    
    def save_emissions_log(self):
        """Save emissions data."""
        os.makedirs(self.output_dir, exist_ok=True)
        log_file = os.path.join(self.output_dir, "emissions.json")
        with open(log_file, 'w') as f:
            json.dump(self.emissions_log, f, indent=2)
    
    def start_tracking(self, job_name: str):
        """Start tracking emissions for a job."""
        try:
            # Try online mode first (with internet)
            self.tracker = EmissionsTracker(
                project_name=f"greengl_{job_name}",
                log_level="WARNING"
            )
        except:
            # Fallback to offline mode
            self.tracker = OfflineEmissionsTracker(
                country_iso_code=self.country_code,
                log_level="WARNING"
            )
        
        self.tracker.start()
        self.current_job = job_name
        self.start_time = datetime.now()
    
    def stop_tracking(self) -> Dict:
        """Stop tracking and return emissions data."""
        if not self.tracker:
            return {}
        
        emissions = self.tracker.stop()
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        record = {
            'job_name': self.current_job,
            'emissions_kg_co2': emissions,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat(),
            'country': self.country_code
        }
        
        self.emissions_log.append(record)
        self.save_emissions_log()
        
        return record
    
    def get_total_emissions(self) -> float:
        """Get cumulative emissions saved."""
        return sum(job['emissions_kg_co2'] 
                  for job in self.emissions_log)
    
    def get_emissions_summary(self) -> Dict:
        """Get emissions summary statistics."""
        if not self.emissions_log:
            return {
                'total_jobs': 0,
                'total_emissions_kg': 0,
                'avg_emissions_per_job_kg': 0,
                'total_duration_hours': 0
            }
        
        df = pd.DataFrame(self.emissions_log)
        
        return {
            'total_jobs': len(df),
            'total_emissions_kg': df['emissions_kg_co2'].sum(),
            'avg_emissions_per_job_kg': df['emissions_kg_co2'].mean(),
            'total_duration_hours': df['duration_seconds'].sum() / 3600,
            'max_single_job_kg': df['emissions_kg_co2'].max(),
            'min_single_job_kg': df['emissions_kg_co2'].min()
        }


# Export
tracker = GPUEmissionsTracker(country_code="IN")
