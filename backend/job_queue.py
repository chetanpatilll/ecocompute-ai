from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from typing import List
import json
import os

class JobStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    DEFERRED = "deferred"

@dataclass
class GPUJob:
    """Represents a GPU job."""
    job_id: str
    name: str
    duration_minutes: int       # Estimated runtime
    power_draw_watts: int       # Est. GPU power draw
    priority: int = 1           # 1=low, 5=high
    status: str = JobStatus.PENDING.value
    carbon_intensity_threshold: int = 400  # Max gCO2/kWh to run
    submitted_at: str = None
    scheduled_for: str = None  # ISO datetime when it should run
    emissions_avoided_kg: float = 0.0
    
    def __post_init__(self):
        if self.submitted_at is None:
            self.submitted_at = datetime.now().isoformat()

class JobQueue:
    """Manages GPU job queue with carbon-aware scheduling."""
    
    def __init__(self, db_file: str = "data/jobs.db"):
        self.db_file = db_file
        self.jobs = []
        self.load_jobs()
    
    def load_jobs(self):
        """Load jobs from JSON."""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                jobs_data = json.load(f)
                self.jobs = [GPUJob(**job) for job in jobs_data]
    
    def save_jobs(self):
        """Save jobs to JSON."""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        with open(self.db_file, 'w') as f:
            json.dump([asdict(job) for job in self.jobs], f, indent=2)
    
    def add_job(self, job: GPUJob) -> str:
        """Add a new job to queue."""
        self.jobs.append(job)
        self.save_jobs()
        return job.job_id
    
    def get_jobs_by_status(self, status: str) -> List[GPUJob]:
        """Get all jobs with given status."""
        return [j for j in self.jobs if j.status == status]
    
    def update_job_status(self, job_id: str, new_status: str):
        """Update job status."""
        for job in self.jobs:
            if job.job_id == job_id:
                job.status = new_status
                self.save_jobs()
                return True
        return False
    
    def get_prioritized_queue(self) -> List[GPUJob]:
        """Get pending jobs sorted by priority."""
        pending = self.get_jobs_by_status(JobStatus.PENDING.value)
        return sorted(pending, key=lambda x: x.priority, reverse=True)
    
    def calculate_emissions_for_job(self, job: GPUJob) -> float:
        """
        Estimate CO2 emissions for a job.
        
        Emissions (kg CO2) = (Power (kW) × Duration (h) × Carbon Intensity (kg CO2/kWh))
        """
        power_kw = job.power_draw_watts / 1000
        duration_h = job.duration_minutes / 60
        
        # Default carbon intensity (can be updated from API)
        carbon_intensity = 0.8  # kg CO2/kWh (depends on region)
        
        emissions = power_kw * duration_h * carbon_intensity
        return emissions


# Export
job_queue = JobQueue()
