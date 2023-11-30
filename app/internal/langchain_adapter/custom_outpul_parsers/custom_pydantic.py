import re
import json
from typing import Type, TypeVar
from nixtlats import TimeGPT


from langchain.output_parsers.format_instructions import PYDANTIC_FORMAT_INSTRUCTIONS
from langchain.schema import OutputParserException, BaseOutputParser
from pydantic import BaseModel, ValidationError
from enum import Enum

T = TypeVar("T", bound="BaseModel")


class CustomPydanticOutputParser(BaseOutputParser[T]):
    """Parse an output using a Pydantic model. that supports parsing enum values on pydantic object"""

    pydantic_object: Type[T]
    """The Pydantic model to parse."""

    def parse(self, text: str) -> T:
        try:
            match = re.search(
                r"\{.*\}", text.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL
            )
            json_str = ""
            if match:
                json_str = match.group()

            json_object = json.loads(json_str, strict=False)

            # Check if the Pydantic model has Enum fields
            enum_fields = {
                name: field
                for name, field in self.pydantic_object.__annotations__.items()
                if isinstance(field, Enum)
            }

            # Convert Enum values to their corresponding Enum instances
            for field_name, enum_class in enum_fields.items():
                if field_name in json_object:
                    json_object[field_name] = enum_class(json_object[field_name])

            # Parse other fields using Pydantic
            return self.pydantic_object.parse_obj(json_object)

        except (json.JSONDecodeError, ValidationError) as e:
            name = self.pydantic_object.__name__
            msg = f"Failed to parse {name} from completion {text}. Got: {e}"
            raise OutputParserException(msg, llm_output=text)

    def get_format_instructions(self) -> str:
        schema = self.pydantic_object.schema()

        # Remove extraneous fields.
        reduced_schema = schema
        if "title" in reduced_schema:
            del reduced_schema["title"]
        if "type" in reduced_schema:
            del reduced_schema["type"]
        # Ensure json in context is well-formed with double quotes.
        schema_str = json.dumps(reduced_schema)

        return PYDANTIC_FORMAT_INSTRUCTIONS.format(schema=schema_str)

    @property
    def _type(self) -> str:
        return "pydantic"