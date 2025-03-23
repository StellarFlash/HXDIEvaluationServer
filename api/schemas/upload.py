from pydantic import BaseModel

class UploadResponse(BaseModel):
    filename: str
    file_path: str 
    document_hash: str
    chunks_count: int
    images_count: int
