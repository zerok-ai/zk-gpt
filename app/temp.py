from prometheus_client.parser import text_string_to_metric_families
from prometheus_client import generate_latest
from io import BytesIO

# Define the string as the input
promql_string = "rate(http_request_duration_seconds_bucket{job=\"kubernetes-service-endpoints\", namespace=\"sofa-shop-mysql\", pod=\"product-56747579fc-b9bk6\", service=\"prometheus-kube-state-metrics\", le=\"+Inf\"}[5m])"

# Convert the string to a Metric Family
metric_families = list(text_string_to_metric_families(promql_string))


print(metric_families)

# Generate a Prometheus metric
metrics_output = BytesIO()
# generate_latest(metrics_output)
promql_query = metrics_output.getvalue().decode("utf-8")

print(promql_query)
