from fastapi import APIRouter,HTTPExecption

from .schemas import MLJobCreate
from .service import create_ml_job, get_ml_job


router =APIRouter(
    prefix="/ml/jobs",
    tags=[MLJob]

)

@router.post("")
def create_job(job:MLJobCreate):
     return create_ml_job(job)



@ router.get("/{job_id}")
def get_job(job_id:str):
    job = get_ml_job(job_id)
    if not job:
        raise HTTPExecption(status_code=404, detail="ML job not found")
    
    return{
        "success":True,
        "job":job
    }