from pydantic import BaseModel


class ImageRequest(BaseModel):
    image_data: str  # base64-encoded PNG

class FiducialRequest(BaseModel):
    position: str # position on page ; can be LU, RU, LD, RD

class CorrectionRequest(BaseModel):
    threshold: int # threshold for binarization