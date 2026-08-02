from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8070)