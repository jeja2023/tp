from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from backend.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="frontend")

@router.get("/map", response_class=HTMLResponse)
async def map_page(request: Request):
    try:
        return templates.TemplateResponse("map.html", {
            "request": request, 
            "map_tile_path": settings.MAP_TILE_PATH,
            "map_default_zoom": settings.MAP_DEFAULT_ZOOM,
            "map_max_zoom": settings.MAP_MAX_ZOOM
        })
    except Exception as e:
        print(f"Error rendering map page: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading map page") 