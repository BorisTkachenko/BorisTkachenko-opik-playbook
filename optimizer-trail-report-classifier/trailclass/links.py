"""Project-pinned Opik UI links."""

import opik


def optimization_link(client: opik.Opik, optimization_id: str) -> str:
    """Direct URL of an optimization run, pinned to its project.

    result.get_run_link() goes through a session redirect that opens in whichever
    project the UI last had active, where the run can look empty. This URL always
    shows the run's trial history.
    """
    info = client.rest_client.optimizations.get_optimization_by_id(optimization_id)
    ui_base = client.config.url_override.rstrip("/").removesuffix("/api")
    return f"{ui_base}/{client.config.workspace}/projects/{info.project_id}/optimizations/{optimization_id}"
