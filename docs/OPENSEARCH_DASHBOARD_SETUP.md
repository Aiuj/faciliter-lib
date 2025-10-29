# OpenSearch Dashboard Setup Guide for OTLP Logs

## Overview

This guide provides complete setup instructions for viewing and monitoring OTLP logs in OpenSearch Dashboards, from initial index configuration through creating production-ready dashboards for application monitoring.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Index Management](#index-management)
3. [Index Patterns and Mappings](#index-patterns-and-mappings)
4. [Discovery and Log Exploration](#discovery-and-log-exploration)
5. [Creating Dashboards](#creating-dashboards)
6. [Useful Dashboards for Application Monitoring](#useful-dashboards-for-application-monitoring)
7. [Alerting and Notifications](#alerting-and-notifications)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Ensure Services Are Running

```bash
# Check all services are up
docker-compose ps

# Should show:
# - opensearch (port 9200)
# - opensearch-dashboards (port 5601)
# - otel-collector (port 4318)
```

### 2. Verify OpenSearch Accessibility

```bash
# Test OpenSearch API
curl -X GET "http://localhost:9200/_cluster/health?pretty" -u admin:admin

# Expected response: status: "green" or "yellow"
```

### 3. Access OpenSearch Dashboards

Open browser to: **http://localhost:5601**

Default credentials:
- Username: `admin`
- Password: `admin` (or as configured in your docker-compose)

---

## Index Management

### Understanding the OTLP Logs Index

Your OTLP collector is configured to send logs to the `otel-logs` index.

### Verify Index Exists

```bash
# List all indices
curl -X GET "http://localhost:9200/_cat/indices?v" -u admin:admin

# Check otel-logs specifically
curl -X GET "http://localhost:9200/otel-logs?pretty" -u admin:admin
```

### View Index Mapping

```bash
# Get current mapping
curl -X GET "http://localhost:9200/otel-logs/_mapping?pretty" -u admin:admin
```

### Index Structure

OTLP logs are stored with this structure:

```json
{
  "@timestamp": "2025-10-29T10:30:45.123Z",
  "observedTimestamp": "2025-10-29T10:30:45.456Z",
  "severityText": "INFO",
  "severityNumber": 9,
  "body": "Application started successfully",
  "resource": {
    "attributes": {
      "service.name": "my-application",
      "service.version": "1.0.0"
    }
  },
  "attributes": {
    "logger.name": "my_app.main",
    "source.file": "/app/main.py",
    "source.line": 42,
    "source.function": "main",
    "user_id": 12345,
    "tenant_id": "acme"
  }
}
```

---

## Index Patterns and Mappings

### Create Index Pattern in Dashboards

1. **Navigate to Stack Management**
   - Click hamburger menu (☰) → **Stack Management**
   - Select **Dashboards management** under "Management"
   - Select **Index Patterns** under "Dashboards management"

2. **Create New Index Pattern**
   - Click **Create index pattern**
   - Index pattern name: `otel-logs*`
   - This matches current and future indices (e.g., `otel-logs`, `otel-logs-2025-10`)

3. **Configure Time Field**
   - Time field: Select `@timestamp`
   - Click **Create index pattern**

### Custom Field Mappings (Optional)

If you need to optimize field types:

```bash
# Create an index template (before data arrives)
curl -X PUT "http://localhost:9200/_index_template/otel-logs-template" \
  -H 'Content-Type: application/json' \
  -u admin:admin \
  -d '{
  "index_patterns": ["otel-logs*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.refresh_interval": "5s"
    },
    "mappings": {
      "properties": {
        "@timestamp": {
          "type": "date"
        },
        "observedTimestamp": {
          "type": "date"
        },
        "severityText": {
          "type": "keyword"
        },
        "severityNumber": {
          "type": "integer"
        },
        "body": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        "resource.attributes.service.name": {
          "type": "keyword"
        },
        "resource.attributes.service.version": {
          "type": "keyword"
        },
        "attributes": {
          "type": "object",
          "dynamic": true
        }
      }
    }
  }
}'
```

### Refresh Field List

After data arrives or mappings change:

1. Go to **Stack Management** → **Index Patterns**
2. Click your `otel-logs*` pattern
3. Click **Refresh field list** (🔄 icon)

---

## Discovery and Log Exploration

### Basic Log Viewing

1. **Open Discover**
   - Click hamburger menu → **Discover**
   - Ensure `otel-logs*` is selected in the dropdown

2. **Set Time Range**
   - Top-right: Click time picker
   - Common ranges: Last 15 minutes, Last 1 hour, Last 24 hours
   - Or use **Absolute** for specific date/time

3. **View Log Details**
   - Click any log entry to expand
   - View all fields in **Table** or **JSON** format

### Searching Logs

#### Simple Text Search

```
# Search in body field
Application started

# Search for errors
error OR exception

# Search specific service
my-application
```

#### Field-Based Queries (KQL - Kibana Query Language)

```
# Filter by severity
severityText: "ERROR"

# Filter by service name
resource.attributes.service.name: "user-service"

# Filter by service version
resource.attributes.service.version: "1.0.0"

# Combine conditions (AND)
severityText: "ERROR" AND resource.attributes.service.name: "api-service"

# Combine conditions (OR)
severityText: "ERROR" OR severityText: "CRITICAL"

# Exclude logs
NOT severityText: "DEBUG"

# Range queries
severityNumber >= 17

# Field exists
attributes.user_id: *

# Specific user
attributes.user_id: 12345

# Wildcard search
attributes.action: "login*"
```

#### OpenSearch Query DSL (Advanced)

Click **Add filter** → **Edit as Query DSL**

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-1h"
            }
          }
        },
        {
          "term": {
            "severityText": "ERROR"
          }
        }
      ],
      "must_not": [
        {
          "match": {
            "body": "test"
          }
        }
      ]
    }
  }
}
```

### Adding Filters

1. **Click "+ Add filter"**
2. Select field (e.g., `severityText`)
3. Choose operator (is, is not, exists, etc.)
4. Enter value
5. Click **Save**

### Selecting Fields to Display

1. **Available Fields** panel (left sidebar)
2. Hover over field name
3. Click **+** to add to table
4. Recommended fields:
   - `@timestamp`
   - `severityText`
   - `body`
   - `resource.attributes.service.name`
   - `attributes.logger.name`
   - `attributes.source.file`
   - `attributes.user_id` (if applicable)

### Saving Searches

1. Click **Save** (top menu)
2. Enter name: "Error Logs - Production"
3. Click **Save**
4. Access saved searches: **Open** button

---

## Creating Dashboards

### Dashboard 1: Application Overview

**Purpose:** High-level view of all application activity

#### Step 1: Create Dashboard

1. Click hamburger menu → **Dashboard**
2. Click **Create dashboard**
3. Click **Add** (+ icon)

#### Step 2: Add Visualizations

**Panel 1: Log Volume Over Time (Line Chart)**

1. **Create visualization** → **Line**
2. **Data:**
   - Index: `otel-logs*`
   - Metrics: Count
   - Buckets:
     - X-axis: Date Histogram
     - Field: `@timestamp`
     - Interval: Auto
3. **Options:**
   - Title: "Log Volume Over Time"
   - Y-axis label: "Log Count"
4. Click **Save and return**

**Panel 2: Logs by Severity (Pie Chart)**

1. **Create visualization** → **Pie**
2. **Data:**
   - Metrics: Count
   - Buckets:
     - Split slices: Terms
     - Field: `severityText`
     - Size: 10
     - Order by: Metric: Count (Descending)
3. **Options:**
   - Title: "Log Distribution by Severity"
   - Show labels: Yes
4. Click **Save and return**

**Panel 3: Top Services (Data Table)**

1. **Create visualization** → **Data table**
2. **Data:**
   - Metrics: Count
   - Buckets:
     - Split rows: Terms
     - Field: `resource.attributes.service.name`
     - Size: 10
3. **Options:**
   - Title: "Top Services by Log Volume"
4. Click **Save and return**

**Panel 4: Recent Errors (Saved Search)**

1. **Add from library**
2. Select your saved search for errors
3. Or create new:
   - **Create visualization** → **Saved search**
   - Filter: `severityText: "ERROR" OR severityText: "CRITICAL"`
   - Fields: `@timestamp`, `severityText`, `body`, `resource.attributes.service.name`
   - Title: "Recent Errors"

#### Step 3: Arrange and Save

1. Drag panels to arrange layout
2. Resize panels as needed
3. Click **Save** (top menu)
4. Name: "Application Overview Dashboard"
5. Click **Save**

---

### Dashboard 2: Error Monitoring

**Purpose:** Detailed error tracking and analysis

#### Visualizations

**1. Error Rate Over Time**

```
Visualization: Line chart
Metrics: Count (filtered by severityText: ERROR or CRITICAL)
X-axis: @timestamp (Date Histogram, Auto interval)
Split series: resource.attributes.service.name
```

**2. Error Distribution by Service**

```
Visualization: Vertical bar chart
Y-axis: Count
X-axis: resource.attributes.service.name
Color by: severityText
```

**3. Top Error Messages**

```
Visualization: Data table
Metrics: Count
Split rows: body.keyword (Terms aggregation, Size: 20)
```

**4. Error Timeline (Heat Map)**

```
Visualization: Heat map
Y-axis: severityText (Terms)
X-axis: @timestamp (Date Histogram, Hourly)
Metric: Count
Color scheme: Red to Yellow
```

**5. Service Health Status**

```
Visualization: Metric
Metrics:
  - Total Errors (Count with severityText: ERROR filter)
  - Critical Errors (Count with severityText: CRITICAL filter)
  - Error Rate (Calculated field if available)
Display: Large numbers with color thresholds
```

**6. Error Details Table**

```
Visualization: Saved search
Filter: severityText: "ERROR" OR severityText: "CRITICAL"
Fields: 
  - @timestamp
  - resource.attributes.service.name
  - severityText
  - body
  - attributes.source.file
  - attributes.source.line
  - attributes.user_id
Sort: @timestamp (descending)
Show: Last 50 errors
```

---

### Dashboard 3: Service Performance

**Purpose:** Monitor individual service health and performance

#### Visualizations

**1. Service Log Volume Trend**

```
Visualization: Area chart
Metrics: Count
X-axis: @timestamp (Date Histogram)
Filters: Add dashboard-level filter or control
  resource.attributes.service.name: [specific service]
```

**2. Severity Breakdown by Time**

```
Visualization: Stacked bar chart
Y-axis: Count
X-axis: @timestamp (Date Histogram, 5-minute intervals)
Split series: severityText
```

**3. Most Active Loggers**

```
Visualization: Horizontal bar chart
X-axis: Count
Y-axis: attributes.logger.name (Terms, Size: 15)
```

**4. Log Messages Word Cloud**

```
Visualization: Tag cloud
Metrics: Count
Tags: body (Terms aggregation)
Size: 50 words
```

**5. Response Time Distribution** (if you log performance metrics)

```
Visualization: Histogram
Metrics: Average (or percentiles)
Field: attributes.duration_ms
Buckets: Histogram with interval 100
```

**6. Service Version Comparison**

```
Visualization: Pie chart or Bar chart
Metrics: Count
Split: resource.attributes.service.version
Filter: Same service name
```

---

### Dashboard 4: User Activity Monitoring

**Purpose:** Track user-related events and actions

#### Prerequisites

Ensure your application logs include user context:

```python
logger.info("User action", extra={
    "user_id": 12345,
    "action": "login",
    "ip_address": "192.168.1.1",
    "tenant_id": "acme"
})
```

#### Visualizations

**1. Active Users Over Time**

```
Visualization: Line chart
Metrics: Unique Count
Field: attributes.user_id
X-axis: @timestamp (Date Histogram)
```

**2. Top Users by Activity**

```
Visualization: Data table
Metrics: Count
Split rows: attributes.user_id (Terms, Size: 20)
Add column: Last activity (@timestamp, Max aggregation)
```

**3. User Actions Distribution**

```
Visualization: Pie chart
Metrics: Count
Split slices: attributes.action (Terms)
```

**4. Geographic Distribution** (if logging IP/location)

```
Visualization: Coordinate map (if geoIP data available)
Or use Data table with:
Split rows: attributes.ip_address or attributes.region
```

**5. Tenant Activity**

```
Visualization: Heat map
Y-axis: attributes.tenant_id (Terms)
X-axis: @timestamp (Date Histogram)
Metrics: Count
```

---

### Dashboard 5: System Health

**Purpose:** Overall system monitoring and alerting

#### Visualizations

**1. Log Rate Gauge**

```
Visualization: Gauge
Metrics: Count (last 5 minutes)
Color ranges:
  - 0-1000: Green (Normal)
  - 1000-5000: Yellow (High)
  - 5000+: Red (Critical)
```

**2. Error Rate Percentage**

```
Visualization: Metric
Metrics: 
  - Total logs: Count
  - Error logs: Count (filter: severityText: ERROR)
  - Calculated: (Error logs / Total logs) * 100
Display: Percentage with threshold colors
```

**3. Service Status Grid**

```
Visualization: Heat map
Y-axis: resource.attributes.service.name
X-axis: severityText
Metrics: Count
Color: Red for errors, green for info
```

**4. Alert Timeline**

```
Visualization: Timeline or Vertical bar chart
Filter: severityText: "ERROR" OR severityText: "CRITICAL"
X-axis: @timestamp (Date Histogram, 1-minute intervals)
Split series: resource.attributes.service.name
```

**5. System Resources** (if logging resource metrics)

```
Visualization: Multiple metrics
Fields: attributes.memory_usage, attributes.cpu_usage, etc.
Display: Line charts with thresholds
```

---

## Adding Dashboard Controls

### Time Range Control

1. **Edit Dashboard**
2. Click **Options** → **Use time filter**
3. Enables time picker for entire dashboard

### Service Filter Control

1. **Edit Dashboard**
2. Click **Add** → **Controls**
3. **Add filter:**
   - Control type: Options list
   - Field: `resource.attributes.service.name`
   - Label: "Select Service"
4. Click **Save and return**

### Severity Filter Control

```
Control type: Options list
Field: severityText
Label: "Log Level"
Allow multiple selections: Yes
```

### Dynamic Filters Example

Create a dashboard with controls panel at the top:

```
Controls:
1. Service selector (resource.attributes.service.name)
2. Severity selector (severityText)
3. Time range picker (built-in)

Visualizations below update automatically when controls change
```

---

## Alerting and Notifications

### Monitor 1: High Error Rate Alert

1. **Navigate to Alerting**
   - Hamburger menu → **Alerting**
   - Click **Create monitor**

2. **Configure Monitor**
   ```
   Monitor name: High Error Rate Alert
   Monitor type: Per query monitor
   Schedule: Every 5 minutes
   
   Query:
   {
     "query": {
       "bool": {
         "must": [
           {
             "range": {
               "@timestamp": {
                 "gte": "now-5m"
               }
             }
           },
           {
             "terms": {
               "severityText": ["ERROR", "CRITICAL"]
             }
           }
         ]
       }
     }
   }
   
   Trigger:
   - Condition: ctx.results[0].hits.total.value > 10
   - Action: Send notification (email, Slack, webhook)
   ```

### Monitor 2: Service Down Detection

```
Monitor name: Service Down - No Logs Received
Schedule: Every 10 minutes

Query: Count logs for specific service in last 10 minutes

Trigger:
- Condition: ctx.results[0].hits.total.value == 0
- Severity: Critical
- Action: Alert operations team
```

### Monitor 3: Critical Error Alert

```
Monitor name: Critical Errors Detected
Schedule: Every 1 minute

Query: Filter severityText: "CRITICAL"

Trigger:
- Condition: ctx.results[0].hits.total.value > 0
- Action: Immediate notification to on-call engineer
```

### Notification Channels

**Configure destinations:**

1. **Go to Alerting** → **Destinations**
2. **Add destination:**

**Email:**
```
Type: Email
Name: DevOps Team Email
Sender: alerts@example.com
Recipients: devops@example.com
```

**Slack:**
```
Type: Slack
Name: DevOps Slack Channel
Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Custom Webhook:**
```
Type: Custom webhook
Name: PagerDuty Integration
URL: https://events.pagerduty.com/v2/enqueue
Headers: Authorization, Content-Type
Body template: Custom JSON payload
```

---

## Best Practices

### 1. Index Lifecycle Management

**Implement index rotation for better performance:**

```bash
# Create ISM policy for monthly rotation
curl -X PUT "http://localhost:9200/_plugins/_ism/policies/otel-logs-policy" \
  -H 'Content-Type: application/json' \
  -u admin:admin \
  -d '{
  "policy": {
    "description": "OTLP logs rotation policy",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [],
        "transitions": [
          {
            "state_name": "warm",
            "conditions": {
              "min_index_age": "7d"
            }
          }
        ]
      },
      {
        "name": "warm",
        "actions": [
          {
            "replica_count": {
              "number_of_replicas": 0
            }
          }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {
              "min_index_age": "30d"
            }
          }
        ]
      },
      {
        "name": "delete",
        "actions": [
          {
            "delete": {}
          }
        ]
      }
    ]
  }
}'
```

### 2. Field Naming Conventions

**Standardize custom attributes across services:**

```python
# Good: Consistent field names
logger.info("User login", extra={
    "user_id": 12345,
    "tenant_id": "acme",
    "action": "login",
    "duration_ms": 150
})

# Avoid: Inconsistent naming
logger.info("User login", extra={
    "userId": 12345,  # camelCase
    "tenant": "acme",  # different name
    "event": "login",  # different name
})
```

### 3. Dashboard Organization

**Create folder structure:**

```
Dashboards/
├── Production/
│   ├── Application Overview
│   ├── Error Monitoring
│   └── System Health
├── Development/
│   ├── Debug Dashboard
│   └── Performance Testing
└── Per-Service/
    ├── API Service Dashboard
    ├── Worker Service Dashboard
    └── Auth Service Dashboard
```

### 4. Query Performance

**Optimize queries:**

- Use specific time ranges (avoid "Last 90 days" for real-time monitoring)
- Filter by service name early in the query
- Use keyword fields for exact matches
- Limit aggregation sizes (Top 10, not Top 1000)
- Refresh dashboard manually when exploring, not every 5 seconds

### 5. Color Coding Standards

**Consistent severity colors:**

```
DEBUG: Gray (#6E6E6E)
INFO: Blue (#3CA7E0)
WARNING: Orange (#F5A623)
ERROR: Red (#E74C3C)
CRITICAL: Dark Red (#C0392B)
```

### 6. Documentation

**Document each dashboard:**

1. Add **Markdown** visualization at top of dashboard
2. Include:
   - Purpose of dashboard
   - Key metrics explanation
   - Alert thresholds
   - Responsible team/contact
   - Last updated date

Example:
```markdown
# Error Monitoring Dashboard

**Purpose:** Real-time tracking of application errors across all services

**Alert Threshold:** >10 errors in 5 minutes triggers alert

**Responsible Team:** Platform Engineering (platform@example.com)

**Last Updated:** 2025-10-29
```

---

## Troubleshooting

### No Data Appearing in OpenSearch

**1. Verify data is being sent:**

```bash
# Check if index has documents
curl -X GET "http://localhost:9200/otel-logs/_count?pretty" -u admin:admin

# Should return: "count": <number>
```

**2. Check OTLP collector:**

```bash
# View collector logs
docker logs otel-collector

# Look for export errors
docker logs otel-collector 2>&1 | grep -i error
```

**3. Verify application is sending logs:**

```python
# Test your faciliter-lib configuration
from faciliter_lib.config import LoggerSettings
from faciliter_lib.tracing.logger import setup_logging

logger_settings = LoggerSettings(
    otlp_enabled=True,
    otlp_endpoint="http://localhost:4318/v1/logs",
    otlp_service_name="test-service",
    log_level="DEBUG",  # Enable debug for testing
)
logger = setup_logging(logger_settings=logger_settings)

logger.info("Test log message")
logger.error("Test error message")
```

### Dashboard Shows "No Results"

**1. Check time range:**
- Ensure time picker includes when logs were sent
- Try "Last 24 hours" or "Last 7 days"

**2. Verify index pattern:**
- Stack Management → Index Patterns
- Check `otel-logs*` has matching indices
- Refresh field list

**3. Check filters:**
- Remove all filters temporarily
- Add filters back one at a time
- Ensure filter values exist in data

### Slow Dashboard Performance

**1. Optimize time range:**
- Use shorter time windows (Last 1 hour vs Last 30 days)
- Use absolute time ranges when possible

**2. Reduce aggregation size:**
- Change "Size: 100" to "Size: 10"
- Limit terms aggregations

**3. Add more specific filters:**
```
# Instead of querying all logs:
# Add filter early:
resource.attributes.service.name: "specific-service"
```

**4. Use time-based indices:**
```
# Instead of: otel-logs (single large index)
# Use: otel-logs-2025-10, otel-logs-2025-11 (monthly indices)
```

### Visualization Not Updating

**1. Force refresh:**
- Click **Refresh** button in dashboard
- Or set auto-refresh interval: Click time picker → Auto-refresh

**2. Clear cache:**
```bash
# Clear OpenSearch cache
curl -X POST "http://localhost:9200/_cache/clear?pretty" -u admin:admin
```

**3. Re-create visualization:**
- Sometimes corrupted saved objects need to be recreated

### Field Not Available for Visualization

**1. Refresh field list:**
- Stack Management → Index Patterns → otel-logs* → Refresh field list

**2. Check field type:**
- Some visualizations require specific types (keyword for terms, date for histograms)

**3. Check field actually exists:**
```bash
curl -X GET "http://localhost:9200/otel-logs/_search?pretty" \
  -H 'Content-Type: application/json' \
  -u admin:admin \
  -d '{
  "size": 1,
  "_source": ["attributes.user_id"]
}'
```

---

## Advanced Tips

### 1. Saved Object Management

**Export dashboards for backup:**

1. Stack Management → Saved Objects
2. Select dashboards to export
3. Click **Export** → Download NDJSON file

**Import dashboards:**

1. Stack Management → Saved Objects
2. Click **Import**
3. Select NDJSON file
4. Resolve conflicts if needed

### 2. Cross-Cluster Search

Monitor logs from multiple OpenSearch clusters:

```bash
# Configure remote cluster
curl -X PUT "http://localhost:9200/_cluster/settings" \
  -H 'Content-Type: application/json' \
  -u admin:admin \
  -d '{
  "persistent": {
    "cluster.remote.prod_cluster.seeds": ["prod-opensearch:9300"]
  }
}'

# Query across clusters
Index pattern: otel-logs*,prod_cluster:otel-logs*
```

### 3. Scripted Fields

Create calculated fields:

1. Stack Management → Index Patterns → otel-logs*
2. **Scripted fields** tab → **Add scripted field**

Example - Error rate:
```
Name: error_rate
Type: number
Script:
  if (doc['severityText'].value == 'ERROR') {
    return 1;
  } else {
    return 0;
  }
```

### 4. Drilldowns

Link dashboards together:

1. Edit visualization
2. Options → **Drilldowns**
3. Add action: Navigate to dashboard
4. Select target dashboard
5. Map filters (e.g., service name)

### 5. Custom Themes

**Change dashboard appearance:**

1. Stack Management → Advanced Settings
2. Search for "theme"
3. Modify colors, fonts, spacing

---

## Example Queries for Common Use Cases

### Find All Errors for Specific User

```
severityText: "ERROR" AND attributes.user_id: 12345
```

### Track Login Attempts

```
attributes.action: "login" OR attributes.action: "logout"
```

### Monitor Database Queries

```
attributes.logger.name: "database" AND attributes.duration_ms > 1000
```

### Find Errors Without Stack Traces

```
severityText: "ERROR" AND NOT attributes.stack_trace: *
```

### Application Startup Events

```
body: "Application started" OR body: "Service initialized"
```

### Failed API Requests

```
attributes.http.status_code >= 400 AND attributes.http.status_code < 600
```

---

## Maintenance Schedule

**Daily:**
- Check Error Monitoring dashboard
- Review System Health dashboard
- Verify all monitors are active

**Weekly:**
- Review dashboard performance
- Check index sizes and growth rate
- Review and update alert thresholds
- Export dashboard backups

**Monthly:**
- Archive or delete old indices
- Review and optimize slow queries
- Update documentation
- Review user access and permissions

---

## Additional Resources

**OpenSearch Documentation:**
- [OpenSearch Dashboards Guide](https://opensearch.org/docs/latest/dashboards/)
- [Query DSL Reference](https://opensearch.org/docs/latest/query-dsl/)
- [Alerting Plugin](https://opensearch.org/docs/latest/monitoring-plugins/alerting/)

**faciliter-lib Documentation:**
- OTLP Integration: `docs/OTLP_LOGGING_INTEGRATION.md`
- Quick Reference: `docs/OTLP_QUICK_REFERENCE.md`
- Examples: `examples/example_otlp_logging.py`

**OpenTelemetry:**
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
- [Log Data Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/)

---

## Summary

You now have a complete setup for monitoring applications with OpenSearch Dashboards:

✅ Index management and mappings configured
✅ Index patterns created for log discovery
✅ Five production-ready dashboards:
   - Application Overview
   - Error Monitoring
   - Service Performance
   - User Activity Monitoring
   - System Health

✅ Alerting configured for critical events
✅ Best practices for performance and organization
✅ Troubleshooting guide for common issues

**Next Steps:**
1. Create your index pattern: `otel-logs*`
2. Import/create the Application Overview dashboard
3. Configure at least one monitor for error alerting
4. Customize dashboards for your specific services
5. Share dashboard URLs with your team

Happy monitoring! 🚀
