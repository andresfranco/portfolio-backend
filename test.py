from fastapi import FastAPI
import logging

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.handlers = [handler]

logger.debug("Test app starting")

@app.get("/")
def root():
    logger.debug("Root hit")
    return {"message": "Test"}

@app.get("/test")
def test():
    logger.debug("Test hit")
    return {"status": "ok"}

@app.get("/error")
def error():
    logger.debug("Error hit")
    raise Exception("Test error")