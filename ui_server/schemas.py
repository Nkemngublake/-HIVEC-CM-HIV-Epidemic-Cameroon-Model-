from pydantic import BaseModel


class StartRequest(BaseModel):
    population: int = 25000
    years: int = 30
    dt: float = 0.1
    start_year: int = 1990
    seed: int | None = 42
    mixing_method: str = 'binned'
    use_numba: bool = False


class StartResponse(BaseModel):
    id: str
    status: str

