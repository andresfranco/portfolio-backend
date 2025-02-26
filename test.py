from fastapi import FastAPI
import logging
import pytest
import smtplib
import ssl
from app.core.config import settings

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

def test_smtp_authentication():
    # Create secure SSL/TLS context
    context = ssl.create_default_context()
    
    try:
        # Attempt to connect and authenticate with SMTP server
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
            # Try to login - this will raise an exception if authentication fails
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            assert True, "SMTP Authentication successful"
            
    except smtplib.SMTPAuthenticationError as e:
        pytest.fail(f"SMTP Authentication failed: {str(e)}")
    except Exception as e:
        pytest.fail(f"Failed to connect to SMTP server: {str(e)}")