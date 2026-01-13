from app.crud.database import db
from fastapi import HTTPException
from app.models.job import Job, JobCreate
from uuid import uuid4


class JobCRUD:
    @staticmethod
    async def create(job: JobCreate, creator_id: str) -> Job:
        """
        Create a new job and link it to the creator user.
        """
        with db.get_session() as session:
            # Generate job ID
            job_id = str(uuid4())

            # Create job in database
            create_result = session.run(
                """
                CREATE (j:Job {
                    id: $id,
                    title: $title,
                    description: $description,
                    contactEmail: $contactEmail,
                    contactPhone: $contactPhone,
                    company: $company,
                    salary: $salary,
                    location: $location,
                    jobType: $jobType,
                    requirements: $requirements,
                    creator_id: $creator_id,
                    status: 'open',
                    created_at: datetime(),
                    updated_at: datetime()
                })
                RETURN j
                """,
                id=job_id,
                title=job.title,
                description=job.description,
                contactEmail=job.contactEmail,
                contactPhone=job.contactPhone,
                company=job.company,
                salary=job.salary,
                location=job.location,
                jobType=job.jobType,
                requirements=job.requirements,
                creator_id=creator_id,
            )
            record = create_result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create job.")

            # Create relationship between user and job
            session.run(
                """
                MATCH (u:User {id: $user_id}), (j:Job {id: $job_id})
                CREATE (u)-[:CREATED]->(j)
                """,
                user_id=creator_id,
                job_id=job_id,
            )

            # Return created job
            job_data = record["j"]
            return Job(
                id=job_data["id"],
                title=job_data["title"],
                description=job_data["description"],
                contactEmail=job_data["contactEmail"],
                contactPhone=job_data.get("contactPhone"),
                company=job_data["company"],
                salary=job_data["salary"],
                location=job_data["location"],
                jobType=job_data["jobType"],
                requirements=job_data.get("requirements"),
                creator_id=job_data["creator_id"],
                status=job_data["status"],
                created_at=job_data["created_at"].isoformat(),
                updated_at=job_data["updated_at"].isoformat() if job_data.get("updated_at") else None,
            )