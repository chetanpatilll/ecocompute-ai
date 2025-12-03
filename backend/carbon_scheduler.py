from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict

from .job_queue import JobQueue, GPUJob, JobStatus
from .carbon_api import carbon_provider
from .emissions_tracker import tracker

class CarbonAwareScheduler:
    """Main scheduler that decides when to run GPU jobs."""
    
    def __init__(self):
        self.job_queue = JobQueue()
        self.carbon_provider = carbon_provider
        self.emissions_tracker = tracker
        self.schedule_history = []
    
    def schedule_pending_jobs(self, region: str = "IN") -> Dict:
        """
        Evaluate pending jobs and schedule/defer based on grid carbon intensity.
        """
        # Get current grid status
        grid_status = self.carbon_provider.get_grid_carbon_intensity(region)
        carbon_intensity = grid_status['carbonIntensity']
        greenness = grid_status['greenness']
        
        pending_jobs = self.job_queue.get_prioritized_queue()
        scheduled_jobs = []
        deferred_jobs = []
        
        for job in pending_jobs:
            if carbon_intensity < job.carbon_intensity_threshold:
                # Green grid - schedule job
                self.job_queue.update_job_status(job.job_id, JobStatus.SCHEDULED.value)
                job.scheduled_for = datetime.now().isoformat()
                scheduled_jobs.append(job)
            else:
                # Dirty grid - defer job
                self.job_queue.update_job_status(job.job_id, JobStatus.DEFERRED.value)
                # Calculate when to reschedule (next 6 hours)
                reschedule_time = datetime.now() + timedelta(hours=6)
                job.scheduled_for = reschedule_time.isoformat()
                deferred_jobs.append(job)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'region': region,
            'current_carbon_intensity': carbon_intensity,
            'grid_greenness': greenness,
            'scheduled_count': len(scheduled_jobs),
            'deferred_count': len(deferred_jobs),
            'total_scheduled_jobs': len(scheduled_jobs),
            'estimated_emissions_saved_kg': sum(
                self.job_queue.calculate_emissions_for_job(j) 
                for j in deferred_jobs
            ),
            'scheduled_jobs': [asdict(j) for j in scheduled_jobs],
            'deferred_jobs': [asdict(j) for j in deferred_jobs]
        }
        
        self.schedule_history.append(result)
        return result
    
    def run_scheduled_job(self, job_id: str) -> Dict:
        """Execute a scheduled job and track emissions."""
        job = next((j for j in self.job_queue.jobs if j.job_id == job_id), None)
        
        if not job:
            return {'error': 'Job not found'}
        
        # Update status to running
        self.job_queue.update_job_status(job_id, JobStatus.RUNNING.value)
        
        # Start emissions tracking
        self.emissions_tracker.start_tracking(job.name)
        
        # Simulate job execution (in real scenario, actually run GPU workload)
        import time
        time.sleep(min(5, job.duration_minutes))  # Simulate for demo
        
        # Stop tracking and get emissions
        emissions_record = self.emissions_tracker.stop_tracking()
        job.emissions_avoided_kg = emissions_record['emissions_kg_co2']
        
        # Mark as completed
        self.job_queue.update_job_status(job_id, JobStatus.COMPLETED.value)
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'emissions_kg_co2': emissions_record['emissions_kg_co2'],
            'duration_seconds': emissions_record['duration_seconds']
        }
    
    def get_dashboard_stats(self) -> Dict:
        """Get stats for dashboard display."""
        total_emissions = self.emissions_tracker.get_emissions_summary()
        pending = len(self.job_queue.get_jobs_by_status(JobStatus.PENDING.value))
        scheduled = len(self.job_queue.get_jobs_by_status(JobStatus.SCHEDULED.value))
        completed = len(self.job_queue.get_jobs_by_status(JobStatus.COMPLETED.value))
        
        return {
            'total_jobs_submitted': len(self.job_queue.jobs),
            'pending': pending,
            'scheduled': scheduled,
            'completed': completed,
            'total_emissions_kg': total_emissions['total_emissions_kg'],
            'emissions_avoided_kg': total_emissions['total_emissions_kg'],  # Approximate
            'avg_job_emissions_kg': total_emissions['avg_emissions_per_job_kg'],
            'schedule_history': self.schedule_history[-10:]  # Last 10 schedules
        }


# Export
scheduler = CarbonAwareScheduler()
