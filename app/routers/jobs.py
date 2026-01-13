from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.job import Job, JobCreate
from ..models import User
from ..crud.jobs import JobCRUD
from app.core.security import get_current_user

router = APIRouter()


@router.get("/jobs/", response_model=List[Job])
async def get_jobs():
    """
    Retrieve the list of all jobs.
    """
    jobs = await JobCRUD.get_all()
    if not jobs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No jobs found.")
    return jobs


@router.post("/jobs/", response_model=Job, status_code=status.HTTP_201_CREATED)
async def create_job(
    job: JobCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new job posting. Requires authentication.
    The authenticated user will be set as the job creator.
    """
    try:
        return await JobCRUD.create(job, creator_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(ex)}",
        )