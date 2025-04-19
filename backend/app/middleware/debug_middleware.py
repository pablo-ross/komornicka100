import time
import json
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class DebugMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, debug_paths: list = None):
        super().__init__(app)
        self.debug_paths = debug_paths or ["/api/strava/auth"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this is a path we want to debug
        should_debug = False
        for path in self.debug_paths:
            if path in request.url.path:
                should_debug = True
                break
        
        if not should_debug:
            return await call_next(request)
        
        # For debug paths, collect request details
        request_time = time.time()
        request_body = None
        
        # Only try to read the body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                request_body = await request.body()
                await request.body()  # Reset request body
            except Exception as e:
                request_body = f"Error reading body: {str(e)}"
        
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Log request info
        print("\n" + "="*50)
        print(f"DEBUG REQUEST: {request.method} {request.url}")
        print(f"Query params: {json.dumps(query_params, indent=2)}")
        if request_body:
            print(f"Request body: {request_body.decode() if isinstance(request_body, bytes) else request_body}")
        print("="*50)
        
        # Process the request
        try:
            response = await call_next(request)
            response_time = time.time() - request_time
            
            # Log response info
            print(f"\nDEBUG RESPONSE: Status {response.status_code} ({response_time:.2f}s)")
            
            # For error responses, try to read the response body
            if response.status_code >= 400:
                response_body = []
                async for chunk in response.body_iterator:
                    response_body.append(chunk)
                
                # Combine the response chunks
                response.body = b"".join(response_body)
                print(f"Response body: {response.body.decode()}")
            
            print("="*50 + "\n")
            return response
        except Exception as e:
            # Log exceptions
            print(f"\nDEBUG EXCEPTION: {str(e)}")
            print("="*50 + "\n")
            raise
            
# Function to add the middleware to your app
def add_debug_middleware(app):
    app.add_middleware(
        DebugMiddleware, 
        debug_paths=["/api/strava/auth"]
    )