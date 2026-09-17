#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: sentry_alert
short_description: Manage a Sentry alert through the monitors and alerts API
description:
  - Creates or updates a metric monitor (detector) and its alert (workflow), or an
    alert on the project's issue stream for new issues.
  - Monitors are matched by name within the project, metric alerts through the
    monitor they are linked to, and issue alerts by name.
options:
  aggregate:
    description: Aggregate of a metric alert, e.g. C(p95(span.duration)).
    type: str
  api_url:
    description: Base API URL, e.g. C(http://127.0.0.1:9000/api/0).
    required: true
    type: str
  critical:
    description: Critical threshold of a metric alert.
    type: float
  dataset:
    default: events_analytics_platform
    type: str
  direction:
    choices: [above, below]
    default: above
    description: Whether the metric alert fires above or below its thresholds.
    type: str
  enabled:
    default: true
    type: bool
  environment:
    default: production
    type: str
  event_types:
    default: [trace_item_span]
    elements: str
    type: list
  extrapolation_mode:
    default: client_and_server_weighted
    type: str
  filters:
    default: []
    description: Extra conditions an issue must match before notifying.
    elements: dict
    type: list
  frequency:
    default: 30
    description: Minimum minutes between notifications of an issue alert.
    type: int
  kind:
    choices: [issue, metric]
    required: true
    type: str
  name:
    required: true
    type: str
  organization:
    required: true
    type: str
  owner:
    description: Owner of a metric monitor, e.g. C(team:1).
    type: str
  project:
    description: Project slug.
    required: true
    type: str
  query:
    default: ""
    type: str
  slack_channel_id:
    description: Without it, Sentry looks the channel up by name through Slack.
    type: str
  slack_channel_name:
    required: true
    type: str
  slack_integration_id:
    required: true
    type: str
  time_window:
    default: 600
    description: Metric alert window in seconds.
    type: int
  token:
    required: true
    type: str
  warning:
    description: Warning threshold of a metric alert.
    type: float
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

PRIORITIES = {"critical": 75, "warning": 50}


class SentryApi:
    def __init__(self, module):
        self.module = module
        self.base = module.params["api_url"].rstrip("/")
        self.headers = {
            "Authorization": "Bearer %s" % module.params["token"],
            "Content-Type": "application/json",
        }

    def request(self, method, path, body=None):
        response, info = fetch_url(
            self.module,
            self.base + path,
            data=json.dumps(body) if body is not None else None,
            headers=self.headers,
            method=method,
            timeout=30,
        )
        content = response.read() if response else info.get("body", b"")
        if info["status"] >= 400 or info["status"] < 200:
            self.module.fail_json(
                msg="%s %s failed with %s" % (method, path, info["status"]),
                body=content.decode("utf-8", "replace") if content else None,
            )
        return json.loads(content) if content else None

    def list(self, path):
        separator = "&" if "?" in path else "?"
        return self.request("GET", "%s%sper_page=100" % (path, separator))


def conditions_for(params):
    above = params["direction"] == "above"
    thresholds = [
        (level, params[level])
        for level in ("critical", "warning")
        if params[level] is not None
    ]
    conditions = [
        {
            "type": "gt" if above else "lt",
            "comparison": value,
            "conditionResult": PRIORITIES[level],
        }
        for level, value in thresholds
    ]
    conditions.append(
        {
            "type": "lte" if above else "gte",
            "comparison": thresholds[-1][1],
            "conditionResult": 0,
        }
    )
    return thresholds, conditions


def slack_action(params, data):
    config = {"targetType": "specific", "targetDisplay": params["slack_channel_name"]}
    if params["slack_channel_id"]:
        config["targetIdentifier"] = params["slack_channel_id"]
    return {
        "type": "slack",
        "integrationId": params["slack_integration_id"],
        "data": data,
        "status": "active",
        "config": config,
    }


def desired_detector(params, workflow_ids):
    _, conditions = conditions_for(params)
    body = {
        "name": params["name"],
        "type": "metric_issue",
        "enabled": params["enabled"],
        "workflow_ids": workflow_ids,
        "data_sources": [
            {
                "aggregate": params["aggregate"],
                "dataset": params["dataset"],
                "environment": params["environment"],
                "eventTypes": params["event_types"],
                "extrapolationMode": params["extrapolation_mode"],
                "query": params["query"],
                "queryType": 1,
                "timeWindow": params["time_window"],
            }
        ],
        "config": {"detectionType": "static"},
        "condition_group": {
            "logicType": "any",
            "conditions": conditions,
            "actions": [],
        },
    }
    if params["owner"]:
        body["owner"] = params["owner"]
    return body


def normalize_detector_body(body):
    source = body["data_sources"][0]
    return {
        "name": body["name"],
        "enabled": body["enabled"],
        "owner": body.get("owner"),
        "query": {
            key: source[key]
            for key in (
                "aggregate",
                "dataset",
                "environment",
                "eventTypes",
                "extrapolationMode",
                "query",
                "timeWindow",
            )
        },
        "conditions": [
            (c["type"], float(c["comparison"]), c["conditionResult"])
            for c in body["condition_group"]["conditions"]
        ],
    }


def normalize_detector(detector, managed_owner):
    query = detector["dataSources"][0]["queryObj"]["snubaQuery"]
    owner = detector.get("owner")
    return {
        "name": detector["name"],
        "enabled": detector["enabled"],
        "owner": (
            "%s:%s" % (owner["type"], owner["id"]) if owner and managed_owner else None
        ),
        "query": {
            key: query.get(key)
            for key in (
                "aggregate",
                "dataset",
                "environment",
                "eventTypes",
                "extrapolationMode",
                "query",
                "timeWindow",
            )
        },
        "conditions": [
            (c["type"], float(c["comparison"]), c["conditionResult"])
            for c in detector["conditionGroup"]["conditions"]
        ],
    }


def desired_workflow(params, detector_id):
    if params["kind"] == "metric":
        thresholds, _ = conditions_for(params)
        return {
            "name": params["name"],
            "enabled": params["enabled"],
            "environment": None,
            "config": {},
            "detector_ids": [int(detector_id)],
            "triggers": {"logicType": "any-short", "conditions": [], "actions": []},
            "action_filters": [
                {
                    "logicType": "any",
                    "conditions": [
                        {
                            "type": condition,
                            "comparison": PRIORITIES[level],
                            "conditionResult": True,
                        }
                        for condition in (
                            "issue_priority_greater_or_equal",
                            "issue_priority_deescalating",
                        )
                    ],
                    "actions": [slack_action(params, {})],
                }
                for level, _ in thresholds
            ],
        }

    return {
        "name": params["name"],
        "enabled": params["enabled"],
        "environment": params["environment"],
        "config": {"frequency": params["frequency"]},
        "detector_ids": [int(detector_id)],
        "triggers": {
            "logicType": "all",
            "conditions": [
                {
                    "type": "first_seen_event",
                    "comparison": True,
                    "conditionResult": True,
                }
            ],
            "actions": [],
        },
        "action_filters": [
            {
                "logicType": "all",
                "conditions": [
                    dict(condition, conditionResult=True)
                    for condition in params["filters"]
                ],
                "actions": [slack_action(params, {"tags": "", "notes": ""})],
            }
        ],
    }


def normalize_filters(filters, with_channel_id):
    return [
        (
            f["logicType"],
            [(c["type"], c["comparison"]) for c in f["conditions"]],
            [
                (
                    a["type"],
                    str(a["integrationId"]),
                    a["config"]["targetDisplay"].lstrip("#"),
                    a["config"].get("targetIdentifier") if with_channel_id else None,
                )
                for a in f["actions"]
            ],
        )
        for f in filters
    ]


def normalize_triggers(triggers):
    if not triggers or not triggers["conditions"]:
        return None
    return (
        triggers["logicType"],
        [(c["type"], c["comparison"]) for c in triggers["conditions"]],
    )


def normalize_workflow_body(body, with_channel_id):
    return {
        "name": body["name"],
        "enabled": body["enabled"],
        "environment": body["environment"],
        "config": body["config"],
        "detectors": sorted(str(d) for d in body["detector_ids"]),
        "triggers": normalize_triggers(body["triggers"]),
        "filters": normalize_filters(body["action_filters"], with_channel_id),
    }


def normalize_workflow(workflow, with_channel_id):
    return {
        "name": workflow["name"],
        "enabled": workflow["enabled"],
        "environment": workflow["environment"],
        "config": workflow["config"] or {},
        "detectors": sorted(str(d) for d in workflow["detectorIds"]),
        "triggers": normalize_triggers(workflow["triggers"]),
        "filters": normalize_filters(workflow["actionFilters"], with_channel_id),
    }


def sync_workflow(module, api, org, workflow_id, detector_id, result):
    body = desired_workflow(module.params, detector_id)
    if workflow_id is None:
        result["changed"] = True
        if not module.check_mode:
            workflow_id = api.request(
                "POST", "/organizations/%s/workflows/" % org, body
            )["id"]
        result["workflow_id"] = workflow_id
        return

    current = api.request("GET", "/organizations/%s/workflows/%s/" % (org, workflow_id))
    with_channel_id = module.params["slack_channel_id"] is not None
    before = normalize_workflow(current, with_channel_id)
    after = normalize_workflow_body(body, with_channel_id)
    result["workflow_id"] = workflow_id
    if before != after:
        result["changed"] = True
        result["diff"].append(
            {
                "before_header": "workflow %s" % workflow_id,
                "after_header": "workflow %s" % workflow_id,
                "before": json.dumps(before, indent=2, sort_keys=True) + "\n",
                "after": json.dumps(after, indent=2, sort_keys=True) + "\n",
            }
        )
        if not module.check_mode:
            api.request(
                "PUT", "/organizations/%s/workflows/%s/" % (org, workflow_id), body
            )


def sync_metric(module, api, org, project_id, result):
    params = module.params
    detectors = api.list("/organizations/%s/detectors/?project=%s" % (org, project_id))
    matches = [
        d
        for d in detectors
        if d["type"] == "metric_issue" and d["name"] == params["name"]
    ]
    if len(matches) > 1:
        module.fail_json(msg="Several monitors are named %s" % params["name"])

    if not matches:
        body = desired_detector(params, [])
        result["changed"] = True
        detector_id = None
        if not module.check_mode:
            detector_id = api.request(
                "POST",
                "/organizations/%s/projects/%s/detectors/" % (org, params["project"]),
                body,
            )["id"]
        result["detector_id"] = detector_id
        sync_workflow(module, api, org, None, detector_id, result)
        return

    detector = api.request(
        "GET", "/organizations/%s/detectors/%s/" % (org, matches[0]["id"])
    )
    workflow_ids = [int(w) for w in detector["workflowIds"]]
    body = desired_detector(params, workflow_ids)
    before = normalize_detector(detector, params["owner"] is not None)
    after = normalize_detector_body(body)
    result["detector_id"] = detector["id"]
    if before != after:
        result["changed"] = True
        result["diff"].append(
            {
                "before_header": "monitor %s" % detector["id"],
                "after_header": "monitor %s" % detector["id"],
                "before": json.dumps(before, indent=2, sort_keys=True) + "\n",
                "after": json.dumps(after, indent=2, sort_keys=True) + "\n",
            }
        )
        if not module.check_mode:
            api.request(
                "PUT", "/organizations/%s/detectors/%s/" % (org, detector["id"]), body
            )

    workflow_id = str(workflow_ids[0]) if workflow_ids else None
    sync_workflow(module, api, org, workflow_id, detector["id"], result)


def sync_issue(module, api, org, project_id, result):
    params = module.params
    streams = [
        d
        for d in api.list("/organizations/%s/detectors/?project=%s" % (org, project_id))
        if d["type"] == "issue_stream"
    ]
    if len(streams) != 1:
        module.fail_json(
            msg="Expected one issue stream monitor in %s, found %d"
            % (params["project"], len(streams))
        )

    matches = [
        w
        for w in api.list("/organizations/%s/workflows/" % org)
        if w["name"] == params["name"]
    ]
    if len(matches) > 1:
        module.fail_json(msg="Several alerts are named %s" % params["name"])

    workflow_id = matches[0]["id"] if matches else None
    result["detector_id"] = streams[0]["id"]
    sync_workflow(module, api, org, workflow_id, streams[0]["id"], result)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            aggregate=dict(type="str"),
            api_url=dict(type="str", required=True),
            critical=dict(type="float"),
            dataset=dict(type="str", default="events_analytics_platform"),
            direction=dict(type="str", default="above", choices=["above", "below"]),
            enabled=dict(type="bool", default=True),
            environment=dict(type="str", default="production"),
            event_types=dict(type="list", elements="str", default=["trace_item_span"]),
            extrapolation_mode=dict(type="str", default="client_and_server_weighted"),
            filters=dict(type="list", elements="dict", default=[]),
            frequency=dict(type="int", default=30),
            kind=dict(type="str", required=True, choices=["issue", "metric"]),
            name=dict(type="str", required=True),
            organization=dict(type="str", required=True),
            owner=dict(type="str"),
            project=dict(type="str", required=True),
            query=dict(type="str", default=""),
            slack_channel_id=dict(type="str"),
            slack_channel_name=dict(type="str", required=True),
            slack_integration_id=dict(type="str", required=True),
            time_window=dict(type="int", default=600),
            token=dict(type="str", required=True, no_log=True),
            warning=dict(type="float"),
        ),
        required_if=[("kind", "metric", ["aggregate"])],
        supports_check_mode=True,
    )
    params = module.params
    if (
        params["kind"] == "metric"
        and params["critical"] is None
        and params["warning"] is None
    ):
        module.fail_json(msg="A metric alert needs a critical or warning threshold")

    api = SentryApi(module)
    org = params["organization"]
    project = api.request("GET", "/projects/%s/%s/" % (org, params["project"]))
    result = dict(changed=False, diff=[])

    if params["kind"] == "metric":
        sync_metric(module, api, org, project["id"], result)
    else:
        sync_issue(module, api, org, project["id"], result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
