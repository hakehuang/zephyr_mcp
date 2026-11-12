#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update projects in a Zephyr west workspace."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Union

import yaml

from src.utils.common_tools import check_tools, run_command
from src.utils.internal_helpers import _west_update_internal
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


NXP_SELECTOR = "nxp"
NXP_MANIFEST_RELATIVE_PATH = os.path.join("boards", "nxp", "west.yaml")


def _normalise_projects(
    projects: Optional[Union[str, List[str]]],
) -> Optional[List[str]]:
    """Return explicit project names, preserving the default full update."""
    if projects is None:
        return None
    if isinstance(projects, str):
        projects = [projects]
    if not isinstance(projects, list) or not projects:
        raise ValueError("projects must be a project name or a non-empty list")
    if not all(isinstance(project, str) and project.strip() for project in projects):
        raise ValueError("each project name must be a non-empty string")
    return [project.strip() for project in projects]


def _nxp_project_filter(project_dir: str) -> Dict[str, Any]:
    """Load the NXP update filter from ``boards/nxp/west.yaml``.

    The file contains a west ``manifest.project-filter`` value. It disables
    non-NXP HAL projects while retaining every non-HAL project and ``hal_nxp``.
    """
    filter_path = os.path.join(project_dir, NXP_MANIFEST_RELATIVE_PATH)
    if not os.path.isfile(filter_path):
        return {
            "status": "error",
            "filter": None,
            "error": f"NXP west filter not found: {filter_path}",
        }

    try:
        with open(filter_path, encoding="utf-8") as stream:
            data = yaml.safe_load(stream) or {}
        project_filter = data["manifest"]["project-filter"]
    except (KeyError, OSError, TypeError, yaml.YAMLError) as error:
        return {
            "status": "error",
            "filter": None,
            "error": f"Invalid NXP west filter {filter_path}: {error}",
        }

    if not isinstance(project_filter, str) or not project_filter.strip():
        return {
            "status": "error",
            "filter": None,
            "error": f"NXP west filter {filter_path} has no project-filter",
        }
    return {"status": "success", "filter": project_filter.strip(), "error": None}


def _filtered_projects(project_dir: str, project_filter: str) -> Dict[str, Any]:
    """Resolve active project names using a west project-filter expression."""
    result = run_command(
        ["west", "list", "--all", "--format", "{name}"], cwd=project_dir
    )
    if result["status"] != "success":
        error = result.get("stderr", "").strip() or "west list failed"
        return {"status": "error", "projects": [], "error": error}

    rules = []
    try:
        for entry in project_filter.split(","):
            entry = entry.strip()
            if entry:
                rules.append((entry[0], re.compile(entry[1:])))
    except (IndexError, re.error) as error:
        return {"status": "error", "projects": [], "error": str(error)}

    projects = []
    for name in result.get("stdout", "").splitlines():
        active = True
        for action, pattern in rules:
            if pattern.fullmatch(name.strip()):
                active = action == "+"
        if active and name.strip() and name.strip() != "manifest":
            projects.append(name.strip())
    return {"status": "success", "projects": projects, "error": None}


def west_update(
    project_dir: str,
    projects: Optional[Union[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Run ``west update`` for all projects or a selected project set.

    Pass ``projects=\"nxp\"`` to read ``boards/nxp/west.yaml`` and update
    all active projects. Its ``project-filter`` excludes non-NXP HAL projects
    while retaining ``hal_nxp`` and every other module. Pass one or more
    native west project names to update those projects directly.

    This is an MCP-tool selector, not a change to west's upstream CLI grammar:
    the resulting command is ``west update <resolved-project-names>``.
    """
    logger.info("[west_update] start project_dir=%s projects=%s", project_dir, projects)

    tools_status = check_tools(["west"])
    if not tools_status.get("west", False):
        return {"status": "error", "log": "", "error": "west tool is not installed"}
    if not os.path.isdir(project_dir):
        return {"status": "error", "log": "", "error": f"Project directory does not exist: {project_dir}"}
    if not os.path.exists(os.path.join(project_dir, "west.yml")):
        return {
            "status": "error",
            "log": "",
            "error": f"west.yml not found; expected a Zephyr manifest repository: {project_dir}",
        }

    try:
        selected_projects = _normalise_projects(projects)
    except ValueError as error:
        return {"status": "error", "log": "", "error": str(error)}

    if selected_projects == [NXP_SELECTOR]:
        filter_result = _nxp_project_filter(project_dir)
        if filter_result["status"] != "success":
            return {"status": "error", "log": [], "error": filter_result["error"]}
        selection = _filtered_projects(project_dir, filter_result["filter"])
        if selection["status"] != "success":
            return {"status": "error", "log": [], "error": selection["error"]}
        selected_projects = selection["projects"]

    result = _west_update_internal(project_dir, selected_projects)
    if result["status"] == "success" and selected_projects is not None:
        result["projects"] = selected_projects
    logger.info("[west_update] finished status=%s", result.get("status"))
    return result
