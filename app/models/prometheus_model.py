# Define your desired data structure.
from typing import List

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


class PrometheusLLMOutputQueries(BaseModel):
    prom_query_list: List[PrometheusQuery] = Field(description="list of all prometheus titles and queries")

    def to_dict(self):
        return {
            "prom_query_list": [query.to_dict() for query in self.prom_query_list]
        }


class PrometheusDataSummarySeverity(BaseModel):
    summary: str = Field(
        description="Summarize the text concisely within 3 or 4 lines in detail, ensuring all key data points "
                    "are addressed")
    severity: str = Field(
        description=f"Attach tag only form the given enum list {', '.join(SeverityEnum._get_all_values_names())} relevance to summary," +
                    f"using the description for each tag from: {', '.join(SeverityEnum.get_all_descriptions())}")

    def to_dict(self):
        prom_summary_severity = {
            "summary": self.summary,
            "severity": self.severity
        }
        return prom_summary_severity


class PrometheusQueryMetricData(BaseModel):
    title: str
    query: str
    metric_data: str

    def to_dict(self):
        prom_metric_data = {
            "title": self.title,
            "query": self.query,
            "metric_data": self.metric_data
        }
        return prom_metric_data

    @classmethod
    def get_prometheus_query_metric_data(cls, prometheus_query: PrometheusQuery, metric_data: str):
        return PrometheusQueryMetricData(query=prometheus_query.query, title=prometheus_query.title
                                         , metric_data=metric_data)


class PrometheusQueryMetricDataSummarySeverity(BaseModel):
    title: str
    query: str
    metric_data: str
    summary: str
    severity: str

    def to_dict(self):
        prom_metric_data = {
            "title": self.title,
            "query": self.query,
            "metric_data": self.metric_data,
            "summary": self.summary,
            "severity": self.severity
        }
        return prom_metric_data

    @classmethod
    def get_prometheus_query_metric_data_summary_severity(cls, prometheus_query_metric_data: PrometheusQueryMetricData,
                                                          prometheus_data_summary_severity: PrometheusDataSummarySeverity):
        return PrometheusQueryMetricDataSummarySeverity(query=prometheus_query_metric_data.query,
                                                        title=prometheus_query_metric_data.title,
                                                        metric_data=prometheus_query_metric_data.metric_data,
                                                        summary=prometheus_data_summary_severity.summary,
                                                        severity=prometheus_data_summary_severity.severity)
