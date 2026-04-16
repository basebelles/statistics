import umpscorecards.pipeline  # noqa: F401 — registers pipeline

from stats_agent.core.registry import get_pipeline, list_pipelines


def test_guardians_umpscorecards_registered():
    p = get_pipeline("guardians-umpscorecards")
    assert p.id == "guardians-umpscorecards"
    assert "guardians-umpscorecards" in list_pipelines()
