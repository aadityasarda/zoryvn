from src.routers.auth import router as auth_router
from src.routers.users import router as users_router
from src.routers.records import router as records_router
from src.routers.dashboard import router as dashboard_router

__all__ = ["auth_router", "users_router", "records_router", "dashboard_router"]
