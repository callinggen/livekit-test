from pydantic import BaseModel

class CallRequest(BaseModel):
    phone: str