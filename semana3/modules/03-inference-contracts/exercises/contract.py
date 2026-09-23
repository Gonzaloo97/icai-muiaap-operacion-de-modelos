from pydantic import BaseModel, ConfigDict, Field


class WineQualityRequest(BaseModel):
    """Input contract for a wine quality inference request."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1, description="Unique identifier of the wine sample.")
    fixed_acidity: float = Field(..., description="Fixed acidity of the wine.")
    volatile_acidity: float = Field(..., example = 0.5, description="Volatile acidity of the wine.")
    citric_acid: float = Field(..., description="Citric acid concentration of the wine.")
    residual_sugar: float = Field(..., description="Residual sugar concentration of the wine.")
    chlorides: float = Field(..., description="Chloride concentration of the wine.")
    free_sulfur_dioxide: float = Field(..., description="Free sulfur dioxide concentration of the wine.")
    total_sulfur_dioxide: float = Field(..., description="Total sulfur dioxide concentration of the wine.")
    density: float = Field(..., description="Density of the wine.")
    ph: float = Field(..., description="pH value of the wine.")
    sulphates: float = Field(..., description="Sulphate concentration of the wine.")
    alcohol: float = Field(..., description="Alcohol content of the wine.")


class WineQualityPrediction(BaseModel):
    """Output contract for a wine quality prediction."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1, description="Identifier of the original wine sample.")
    quality_band: str = Field(..., description="Quality category predicted by the model.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score associated with the prediction.")
    model_version: str = Field(..., description="Version of the model used for inference.")
    preprocessing_version: str = Field(..., description="Version of the preprocessing pipeline used for inference.")

