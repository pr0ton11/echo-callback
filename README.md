# Echo-Callback Server

This is a service:

* That you can request your endpoint with a call to /
* That you can post data to the same endpoint (e.g oauth2-redirect data)
* Retrieve the same data with another get request (which also deletes the endpoint again from the server)
* Cleans up all the endpoints that are older than CLEANUP_ENDPOINTS_MIN (default: 5 mins)

It is used to securely retrieve oauth2 tokens without redirecting the user to localhost (which would be insecure)

It can be used for other types of temporary data as well
