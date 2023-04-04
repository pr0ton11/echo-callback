import asyncio
import datetime
import uuid
import os

from hypercorn.config import Config
from hypercorn.asyncio import serve

from starlette.requests import Request

from fastapi import FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every

CLEANUP_ENDPOINTS_MIN = 5  # How many minutes the server waits to cleanup old endpoints

ENV_BEHIND_PROXY = "BEHIND_PROXY" # env to set http:// to https:// replacement
IS_BEHIND_PROXY = os.getenv(ENV_BEHIND_PROXY, "false").lower() == "true"

endpoints = {}  # In memory endpoint data

app = FastAPI()  # FastAPI app instance

def replace_protocol(url: str) -> str:
    """
    Replaces protocol in url and returns it
    """

    if IS_BEHIND_PROXY:
        return url.replace("http://", "https://")

    return url

class Endpoint:
    """
    Defines an endpoint that the server accepts messages
    """
    def __init__(self):
        self.id = self.generate_random_id()
        self.data = {}
        self.timestamp = datetime.datetime.now()

    def generate_random_id(self):
        return str(uuid.uuid4())

@app.get("/")
async def get_endpoint(request: Request):
    # Generate a new endpoint
    endpoint = Endpoint()
    # Add endpoint to dict
    endpoints[endpoint.id] = endpoint
    # Return the URL
    return {"url": f"{replace_protocol(request.url)}{endpoint.id}"}

@app.post("/{endpoint}")
async def write_data(endpoint: str, request: Request):
    """
    Writes the data from the post request to the in memory dict
    """
    if endpoint not in endpoints:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    if bool(endpoints[endpoint].data):
        raise HTTPException(status_code=403, detail="Data has already been written to this endpoint")
    endpoints[endpoint].data = await request.json()
    return {"msg": f"Sucessfully written your data to key {endpoint}"}

@app.get("/{endpoint}")
async def get_data(endpoint: str):
    """ 
    Retrieves the data from the in memory dict and sends it to the client
    """
    if endpoint not in endpoints:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    if not bool(endpoints[endpoint].data):
        raise HTTPException(status_code=425, detail="Data has not been written to this endpoint yet")
    data = endpoints[endpoint].data
    del endpoints[endpoint]
    return data

@repeat_every(seconds=CLEANUP_ENDPOINTS_MIN*60)
def remove_expired_endpoints() -> None:
    """
    Removes expired endpoints
    """
    for key in endpoints:
        endpoint = endpoints[key]
        diff = datetime.datetime.now() - endpoint.timestamp
        if diff.minutes() > CLEANUP_ENDPOINTS_MIN:
            del endpoints[key]

if __name__ == "__main__":
    """
    Entrypoint
    """
    config = Config()
    config.bind = "[::]:3000"
    asyncio.run(serve(app, config))
