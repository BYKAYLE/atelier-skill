from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path("~/.claude/skills/release/scripts").expanduser()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from service_factory import build_agent_requests, build_state, stage_spec_map, validate_state  # noqa: E402


def test_research_intelligence_stage_is_between_current_state_and_development_plan():
    spec = stage_spec_map()
    assert "research_intelligence" in spec
    assert spec["research_intelligence"][2] == ["current_state"]
    assert spec["development_plan"][2] == ["research_intelligence"]


def test_research_lane_agent_requests_are_materialized_and_available():
    state = build_state(Path("/private/tmp/stella-research-factory-test"), "Build a research-backed autonomous product", "factory")
    requests, missing = build_agent_requests(state)
    request_ids = {request["id"] for request in requests}
    assert {
        "research_intelligence::research_director",
        "research_intelligence::market_researcher",
        "research_intelligence::evidence_synthesizer",
        "research_intelligence::methodology_reviewer",
    }.issubset(request_ids)
    missing_agents = {item["agent_type"] for item in missing}
    assert "k-dense-researcher" not in missing_agents
    assert "research-methodologist" not in missing_agents


def test_operating_contract_requires_research_before_plan():
    state = build_state(Path("/private/tmp/stella-research-factory-test"), "Build a research-backed autonomous product", "factory")
    errors, _warnings = validate_state(state)
    assert not errors
    assert state["operating_contract"]["required_order"] == [
        "current_state",
        "research_intelligence",
        "development_plan",
        "execution_verification",
    ]
