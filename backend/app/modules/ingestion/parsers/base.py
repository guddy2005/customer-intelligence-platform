from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_content: str) -> Generator[Dict[str, Any], None, None]:
        """Reads file content and yields dictionaries per row."""
        pass
