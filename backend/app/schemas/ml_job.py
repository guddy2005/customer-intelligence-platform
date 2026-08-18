from typing import any
from pydantic import BaseModel,Field

class MLJobCreate(BaseModel):
    engine: str = Field(..., description="The ML engine to use for the job")
    model: str = Field(..., description="The specific model to be used for the job")
    dataset_id: str = Field(..., description="The ID of the dataset to be used for training or inference")
    features: list[str] = Field(..., description="List of features to be used in the ML job")
    parameters: dict[str, any] = Field(..., description="Additional parameters for the ML job")