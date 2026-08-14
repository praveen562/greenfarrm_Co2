from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)

    fertilizer_usage: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_consumption: Mapped[float] = mapped_column(Float, nullable=False)
    water_consumption: Mapped[float] = mapped_column(Float, nullable=False)
    electricity_consumption: Mapped[float] = mapped_column(Float, nullable=False)

    predicted_carbon: Mapped[float] = mapped_column(Float, nullable=False)
    carbon_category: Mapped[str] = mapped_column(String(20), nullable=False)
    sustainability_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Phase 13

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    farm: Mapped["Farm"] = relationship(back_populates="predictions")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="prediction", cascade="all, delete-orphan"
    )
