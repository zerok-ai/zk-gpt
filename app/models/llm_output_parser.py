# Define your desired data structure.
from typing import List, Type

from pydantic import BaseModel, Field

from app.models.enums.severity_enum import SeverityEnum


class PrometheusQuery(BaseModel):
    title: str = Field(description="prometheus query description as title")
    query: str = Field(description="prometheus query")

    def to_dict(self):
        prom_query = {
            "title": self.title,
            "query": self.query
        }
        return prom_query


class PrometheusLLMOutputParser(BaseModel):
    prom_query_list: List[PrometheusQuery] = Field(description="list of all prometheus queries")

    def to_dict(self):
        return {
            'prom_query_list': [query.to_dict() for query in self.prom_query_list]
        }


class PrometheusDataSummary(BaseModel):
    summary: str = Field(
        description="Summarize the text concisely within 3 or 4 lines in detail, ensuring all key data points "
                    "are addressed")
    label: str = Field(description=f"Attach tag only form the given enum list {', '.join(SeverityEnum._get_all_values_names())} relevance to summary," +
                                   f"using the description for each tag from: {', '.join(SeverityEnum.get_all_descriptions())}")

    def to_dict(self):
        prom_summary = {
            "summary": self.summary,
            "label": self.label
        }
        return prom_summary

