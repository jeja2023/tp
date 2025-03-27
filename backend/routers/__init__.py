# 路由包初始化文件 

# Import all routers
from .base import router as base_router
from .users import router as users_router, oauth2_router
from .tasks import router as tasks_router
from .images import router as images_router 