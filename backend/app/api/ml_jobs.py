from fastapi import APIRouter, HTTPExecption 
from uuid import uuid4

import app.schemas.ml_job # type: ignore

router = APIRouter(
    prefix ="/api/ml/jobs",
    tags=["ml_jobs"]
)


jobs={}

@router.post("")
def create_ml_job(job: app.schemas.ml_job.MLJobCreate):

    job_id = f"JOB_{uuid4().hex[:8].upper()}"

    job_data = {
    "job_id" : job_id,
    "engine" : job.engine,
    "model": job.model,
    "dataset_id":job.dataset_id, 
    "features" :job.features,
    "parameters":job.parameters,
    "status":"PENDING"
    }

    jobs[job_id]=job_data

    return{
        "sucess":True,
        "Message":"ML job created successfully",
        "job":job_data
    }

@router.get("/{job_id}")
def get_ml_job(job_id:str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPExecption(status_code=404, detail="ML job not found")
    
    return{
        "success":True,
        "job":job
    }