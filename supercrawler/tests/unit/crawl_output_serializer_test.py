from supercrawler.crawl_output_serializer import serialize_configuration, serialize_crawl_output
from supercrawler.model.page import Page
from supercrawler.model.page_content import PageContent
from supercrawler.model.page_exploration_result import PageExplorationResult
from supercrawler.model.page_id import PageId


def test_serialize_crawl_output_includes_configuration_and_results() -> None:
    configuration = serialize_configuration(
        url="https://example.com",
        log_level="DEBUG",
        persist_logs=False,
        max_concurrency=10,
    )
    results = [
        PageExplorationResult(
            url="https://example.com",
            status="success",
            page=Page(
                id=PageId("page-1"),
                url="https://example.com",
                content=PageContent(["https://example.com/about"]),
            ),
        ),
        PageExplorationResult(
            url="https://example.com/error",
            status="failure",
            error="boom",
        ),
    ]

    serialized_output = serialize_crawl_output(
        configuration=configuration,
        started_at="2026-04-15T12:00:00+00:00",
        logs_filepath="/tmp/supercrawler.logs",
        duration_seconds=1.25,
        results=results,
    )

    assert serialized_output == {
        "configuration": {
            "url": "https://example.com",
            "log_level": "DEBUG",
            "persist_logs": False,
            "max_concurrency": 10,
        },
        "started_at": "2026-04-15T12:00:00+00:00",
        "logs_filepath": "/tmp/supercrawler.logs",
        "duration_seconds": 1.25,
        "results": [
            {
                "url": "https://example.com",
                "status": "success",
                "page_content": {
                    "links": ["https://example.com/about"],
                },
                "error": None,
            },
            {
                "url": "https://example.com/error",
                "status": "failure",
                "page_content": None,
                "error": "boom",
            },
        ],
    }
