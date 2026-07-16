from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "service": "AI Voice Platform",
    }