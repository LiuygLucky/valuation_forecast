from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Money(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    amount_raw: Decimal = Field(gt=0)
    currency: str
    scale: Decimal = Field(gt=0)
    amount_usd: Decimal | None = None
    fx_rate: Decimal | None = Field(default=None, gt=0)
    fx_rate_source_id: str | None = None

    @model_validator(mode="after")
    def convert(self):
        if self.currency == "USD":
            expected = self.amount_raw * self.scale
        elif self.fx_rate is not None and self.fx_rate_source_id:
            expected = self.amount_raw * self.scale * self.fx_rate
        else:
            if self.amount_usd is not None:
                raise ValueError("reliable FX source required")
            return self
        if self.amount_usd is not None and self.amount_usd != expected:
            raise ValueError("inconsistent USD conversion")
        self.amount_usd = expected
        return self
