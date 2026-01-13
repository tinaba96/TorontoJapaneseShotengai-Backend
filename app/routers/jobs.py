from fastapi import APIRouter, Depends, HTTPException, status
from ..models.job import Job, JobCreate
from ..models import User
from ..crud.jobs import JobCRUD
from app.core.security import get_current_user

router = APIRouter()


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