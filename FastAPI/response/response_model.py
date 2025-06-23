from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TickerResponse(BaseModel):
    tickers : List[Dict[str, Any]]
    message : str