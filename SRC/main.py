# Author: Diego Dominguez Garcia
# Date: 03/12/2023

# import primary modules for FastAPI
from fastapi import FastAPI, Body
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse

# Import modules to create astromap
from Modules import SkyMap

# Import database models and connection
from database import Map
from database import database as connection

# Import schemas for get multiple data
import schemas

# Create a logger
import logging

# Create and configure logger
logging.basicConfig(filename='Data/Logs/API.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s'
                    )

# Create an instance of the FastAPI class
app = FastAPI(title="AstroMap API", version="0.0.1", description="Astromap API generated to create astromap images", docs_url=None, redoc_url=None)
# Create an instance of the SkyMap class, this class is used to create astromap images
skymap = SkyMap.StarCharts()


# Create a startup event to connect to the database
@app.on_event("startup")
def startup():
    if not connection.is_closed():
        connection.connect()

    connection.create_tables([Map])


# Create a shutdown event to close the connection to the database
@app.on_event("shutdown")
def shutdown():
    if not connection.is_closed():
        connection.close()


# Create a route to create a map
@app.post("/create_map")
async def generate_map(background_tasks: BackgroundTasks, map_schema: schemas.Map_Schema = Body(...)):
    try:
        background_tasks.add_task(skymap.create, location=map_schema.Location, when=map_schema.Date_Time, MapModel=Map, User_UID=map_schema.UserUID, Map_UID=map_schema.MapUID)

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


# Create a route to check the status of a map
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
