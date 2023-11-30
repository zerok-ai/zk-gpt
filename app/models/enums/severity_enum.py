from enum import Enum
from typing import Dict, List

from langchain.output_parsers import EnumOutputParser


class SeverityEnum(Enum):
    Critical = {
        'value': "Critical",
        'description': "Critical issue requires immediate attention"
    }
    Major = {
        'value': "Major",
        'description': "Major issue, significant blocking problem"
    }
    Minor = {
        'value': "Minor",
        'description': "Minor issue, may affect customers but no one is blocked"
    }
    Pending = {
        'value': "Pending",
        'description': "Pending issue, severity to be decided"
    }
    Normal = {
        'value': "Normal",
        'description': "Normal, no significant issues identified"
    }

    @classmethod
    def _valid_values_descriptions(cls) -> List[Dict[str, str]]:
        return [member.value for member in cls]

    @classmethod
    def _valid_values_descriptions_str(cls) -> str:
        result = "\n".join([f"{value['value']}: {value['description']}" for value in cls._valid_values_descriptions()])
        return result

    @classmethod
    def _get_all_values_names(cls):
        return [member.name for member in cls]

    @classmethod
    def get_all_enums(cls):
        return [member.value for member in cls]

    @classmethod
    def get_all_descriptions(cls):
        return [member.value.get("description") for member in cls]

