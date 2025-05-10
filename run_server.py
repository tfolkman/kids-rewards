import sys
import os
import uvicorn

if __name__ == "__main__":
    # Add the project root to sys.path
    # This ensures that 'backend' can be imported as a top-level package
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Now that sys.path is set up, we can import the app
    # Uvicorn will be called with the application string 'backend.main:app'
    # and it should find it correctly.
    # Temporarily disabling reload to isolate the issue.
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)