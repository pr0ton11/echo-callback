#!/usr/bin/env python3

# echo-callback: A service to keep and distribute oauth tokens outside the browser

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>. 

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

ENV_BEHIND_PROXY = "BEHIND_HTTPS_PROXY" # env to set http:// to https:// replacement
IS_BEHIND_PROXY = os.getenv(ENV_BEHIND_PROXY, "false").lower() == "true"

endpoints = {}  # In memory endpoint data

app = FastAPI()  # FastAPI app instance

def replace_protocol(url) -> str:
    """
    Replaces protocol in url and returns it
    """

    str_url = str(url)

    if IS_BEHIND_PROXY:
        return str_url.replace("http://", "https://")

    return str_url

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
    return {"msg": f"Sucessfully written your data to key {endpoint}, you can close this window"}

@app.get("/{endpoint}")
async def get_data(endpoint: str, code: str | None = None, state: str | None = None):
    """ 
    Retrieves the data from the in memory dict and sends it to the client
    When code and state is defined as param, write this data instead to the data endpoint
    """
    if endpoint not in endpoints:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    if code and state:
        endpoints[endpoint].data = {
            "code": code,
            "state": state
        }
        return {"msg": f"Sucessfully written your data to key {endpoint}, you can close this window"}
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
