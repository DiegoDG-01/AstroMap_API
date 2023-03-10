from fastapi import FastAPI, Response
from fastapi import Request
from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse

from Modules import SkyMap

from database import database as connection
from database import Map

import logging


logging.basicConfig(filename='Data/Logs/API.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s'
                    )


app = FastAPI(title="AstroMap API", version="0.0.1", description="Astromap API generated to create astromap images", docs_url=None, redoc_url=None)
skymap = SkyMap.StarCharts()


@app.on_event("startup")
def startup():
    if not connection.is_closed():
        connection.connect()

    connection.create_tables([Map])


@app.on_event("shutdown")
def shutdown():
    if not connection.is_closed():
        connection.close()


# Get other data from the database to create the map
@app.post("/create_map", response_class=JSONResponse)
async def generate_map(background_tasks: BackgroundTasks, request: Request):
    try:
        data = await request.json()
        background_tasks.add_task(skymap.create, location=data['location'], when=data['date_time'], MapModel=Map,
                                  User_UID=data['uuid'], Map_UID=data['map_uuid'])

        return {
            "created": True,
            "message": "The map is being created",
            "time_estimated": "5 minutes"
        }
    except Exception as e:
        logging.error(e)
        return {
            "created": False,
            "error": "An error has occurred",
        }


@app.get("/check_status/{id}")
async def check_status(id: str):

    map = Map.get(Map.map_uuid == id)

    if map.status == 'created':

        # crear un generador de bytes para transmitir la imagen
        return FileResponse(map.url, media_type="image/png")

    elif map.status == 'in_progress':
        return {
            "status": "in_progress",
            "message": "The map is being created",
            "time_estimated": "5 minutes"
        }
    else:
        return {
            "status": "error",
            "message": "An error has occurred",
            "error": map.status
        }
