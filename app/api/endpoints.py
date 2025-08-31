from fastapi import APIRouter
router = APIRouter()

@router.get("/health", tags=["status"])
def health_check():
    return {"status": "ok", "message": "RLx service is running"}
