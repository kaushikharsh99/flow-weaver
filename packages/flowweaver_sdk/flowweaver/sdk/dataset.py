import abc
from typing import List, Dict, Any, Optional

class Dataset(abc.ABC):
    @abc.abstractmethod
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert dataset to list of dicts (tabular)."""
        pass

    @abc.abstractmethod
    def columns(self) -> List[str]:
        """Return list of dataset columns."""
        pass
        
    @abc.abstractmethod
    def row_count(self) -> int:
        """Return number of rows."""
        pass

class TabularDataset(Dataset):
    """Standard in-memory list-of-dicts tabular dataset."""
    def __init__(self, data: List[Dict[str, Any]], columns: Optional[List[str]] = None):
        self._data = data
        if columns is not None:
            self._columns = columns
        else:
            self._columns = list(data[0].keys()) if data else []
        
    def to_list(self) -> List[Dict[str, Any]]:
        return self._data
        
    def columns(self) -> List[str]:
        return self._columns
        
    def row_count(self) -> int:
        return len(self._data)
