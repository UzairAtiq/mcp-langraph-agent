# backwards compatibility wrapper for api.main imports
from main import app

# run uvicorn server directly if executed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
