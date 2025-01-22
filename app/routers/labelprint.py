from fastapi import APIRouter, Request
from app.database import db
from pydantic import BaseModel


router = APIRouter(
    prefix="/labelprint",
    tags=["labelprint"],
)


# ---- API Endpoints ----

class PrintData(BaseModel):
    barcodeText: str
    labelText: str
    dateText: str
    noteText: str | None = None  # Optional noteText
    RestrictiveLabel: bool

    
from app.service.labelprinter import print_label
@router.post("/")
async def cloud_print_label(print_data: PrintData, request: Request):
    """
    Endpoint to process print data
    """
    try:
        print_label(print_data)
        # print(print_data.model_dump())
        return {"message": "Print request received successfully"}

    except Exception as e:
        return {"error": str(e)}