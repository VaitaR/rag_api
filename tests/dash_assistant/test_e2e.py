# tests/dash_assistant/test_e2e.py
"""End-to-end integration tests for dash assistant."""
import os
import pytest
import pytest_asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Set test environment before importing app modules
os.environ["TESTING"] = "1"
os.environ["EMBEDDINGS_PROVIDER"] = "MOCK"

from app.main import app
from app.dash_assistant.db import DashAssistantDB
from app.dash_assistant.ingestion.index_jobs import IndexJob


@pytest_asyncio.fixture
async def e2e_client(clean_db, mock_index_job, monkeypatch):
    """Create test client with mocked database for E2E tests."""
    # Mock health check to return True
    async def mock_health_check():
        return True
    
    monkeypatch.setattr(DashAssistantDB, "health_check", mock_health_check)
    
    # Create test client
    with TestClient(app) as client:
        yield client


@pytest.fixture
def e2e_fixtures_dir():
    """Get path to E2E test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures" / "superset"


@pytest_asyncio.fixture
async def ingested_data(e2e_client, e2e_fixtures_dir, mock_index_job):
    """Fixture that runs full ingestion pipeline with E2E test data."""
    # Prepare file paths
    dashboards_csv = e2e_fixtures_dir / "e2e_dashboards.csv"
    charts_csv = e2e_fixtures_dir / "e2e_charts.csv"
    md_dir = e2e_fixtures_dir / "e2e_md"
    enrichment_yaml = e2e_fixtures_dir / "e2e_enrichment.yaml"
    
    # Verify files exist
    assert dashboards_csv.exists(), f"Missing {dashboards_csv}"
    assert charts_csv.exists(), f"Missing {charts_csv}"
    assert md_dir.exists(), f"Missing {md_dir}"
    assert enrichment_yaml.exists(), f"Missing {enrichment_yaml}"
    
    # Run ingestion via API endpoint
    ingestion_request = {
        "dashboards_csv": str(dashboards_csv),
        "charts_csv": str(charts_csv),
        "md_dir": str(md_dir),
        "enrichment_yaml": str(enrichment_yaml),
        "run_embeddings": True
    }
    
    response = e2e_client.post("/dash/ingest", json=ingestion_request)
    assert response.status_code == 200, f"Ingestion failed: {response.text}"
    
    ingestion_result = response.json()
    assert ingestion_result["status"] == "success"
    
    # Verify data was loaded
    assert ingestion_result["results"]["dashboards_loaded"] == 2
    assert ingestion_result["results"]["charts_loaded"] == 4
    assert ingestion_result["results"]["markdown_processed"] == 2
    assert ingestion_result["results"]["dashboards_enriched"] == 2
    assert ingestion_result["results"]["chunks_indexed"] > 0
    
    return ingestion_result


# Query logging is now built into the endpoint, no need for separate fixture


class TestE2EIntegration:
    """End-to-end integration tests."""
    
    @pytest_asyncio.async_test
    async def test_full_pipeline_with_feedback(self, ingested_data, e2e_client):
        """Test complete pipeline: ingestion → query → feedback logging.
        
        This test:
        1. Uses pre-ingested data (2 dashboards: product retention, marketing funnel)
        2. Queries for 'retention' and expects 'User Retention Dashboard' as top result
        3. Records feedback for the result and verifies it's logged in query_log
        """
        # Step 1: Query for 'retention' - should return User Retention Dashboard as top result
        query_request = {
            "q": "retention",
            "top_k": 3
        }
        
        query_response = e2e_client.post("/dash/query", json=query_request)
        assert query_response.status_code == 200, f"Query failed: {query_response.text}"
        
        query_result = query_response.json()
        
        # Verify we got results
        assert len(query_result["results"]) > 0, "No results returned"
        
        # Verify top result is User Retention Dashboard
        top_result = query_result["results"][0]
        assert "retention" in top_result["title"].lower(), f"Expected retention dashboard, got: {top_result['title']}"
        
        # Get qid from debug info
        qid = query_result["debug"]["qid"]
        assert qid is not None and qid > 0, "Query ID not returned"
        
        # Get entity_id from top result
        entity_id = top_result.get("entity_id")
        assert entity_id is not None, "Entity ID not found in result"
        
        # Step 2: Record positive feedback for the top result
        feedback_request = {
            "qid": qid,
            "entity_id": entity_id,
            "feedback": "up"
        }
        
        feedback_response = e2e_client.post("/dash/feedback", json=feedback_request)
        assert feedback_response.status_code == 200, f"Feedback failed: {feedback_response.text}"
        
        feedback_result = feedback_response.json()
        assert feedback_result["status"] == "success"
        
        # Step 3: Verify feedback was logged in database
        logged_feedback = await DashAssistantDB.fetch_one("""
            SELECT qid, query_text, chosen_entity, feedback
            FROM query_log 
            WHERE qid = $1
        """, qid)
        
        assert logged_feedback is not None, "Feedback not found in query_log"
        assert logged_feedback["qid"] == qid
        assert logged_feedback["query_text"] == "retention"
        assert logged_feedback["chosen_entity"] == entity_id
        assert logged_feedback["feedback"] == "up"
        
    @pytest_asyncio.async_test 
    async def test_marketing_funnel_query(self, ingested_data, e2e_client):
        """Test query for marketing funnel returns correct dashboard."""
        query_request = {
            "q": "marketing funnel",
            "top_k": 2
        }
        
        query_response = e2e_client.post("/dash/query", json=query_request)
        assert query_response.status_code == 200
        
        query_result = query_response.json()
        assert len(query_result["results"]) > 0
        
        # Should find marketing performance dashboard
        top_result = query_result["results"][0]
        assert "marketing" in top_result["title"].lower()
        
        # Test negative feedback
        qid = query_result["debug"]["qid"]
        entity_id = top_result.get("entity_id")
        
        feedback_request = {
            "qid": qid,
            "entity_id": entity_id,
            "feedback": "down"
        }
        
        feedback_response = e2e_client.post("/dash/feedback", json=feedback_request)
        assert feedback_response.status_code == 200
        
        # Verify negative feedback logged
        logged_feedback = await DashAssistantDB.fetch_one("""
            SELECT feedback FROM query_log WHERE qid = $1
        """, qid)
        
        assert logged_feedback["feedback"] == "down"
        
    @pytest_asyncio.async_test
    async def test_chart_specific_feedback(self, ingested_data, e2e_client):
        """Test feedback with specific chart_id."""
        query_request = {
            "q": "cohort analysis",
            "top_k": 1
        }
        
        query_response = e2e_client.post("/dash/query", json=query_request)
        assert query_response.status_code == 200
        
        query_result = query_response.json()
        top_result = query_result["results"][0]
        
        # Get chart from result if available
        charts = top_result.get("charts", [])
        chart_id = None
        if charts:
            chart_id = charts[0].get("chart_id")
        
        qid = query_result["debug"]["qid"]
        entity_id = top_result.get("entity_id")
        
        feedback_request = {
            "qid": qid,
            "entity_id": entity_id,
            "chart_id": chart_id,
            "feedback": "up"
        }
        
        feedback_response = e2e_client.post("/dash/feedback", json=feedback_request)
        assert feedback_response.status_code == 200
        
        # Verify chart_id was logged
        logged_feedback = await DashAssistantDB.fetch_one("""
            SELECT chosen_entity, chosen_chart FROM query_log WHERE qid = $1
        """, qid)
        
        assert logged_feedback["chosen_entity"] == entity_id
        if chart_id:
            assert logged_feedback["chosen_chart"] == chart_id
            
    @pytest_asyncio.async_test
    async def test_health_and_stats_endpoints(self, ingested_data, e2e_client):
        """Test health and stats endpoints work with ingested data."""
        # Test health endpoint
        health_response = e2e_client.get("/dash/health")
        assert health_response.status_code == 200
        
        health_result = health_response.json()
        assert health_result["status"] == "healthy"
        assert health_result["database"] == "connected"
        
        # Test stats endpoint
        stats_response = e2e_client.get("/dash/stats")
        assert stats_response.status_code == 200
        
        stats_result = stats_response.json()
        assert stats_result["dashboards"] == 2
        assert stats_result["charts"] == 4
        assert stats_result["chunks"] > 0
        assert stats_result["chunks_with_embeddings"] > 0
        assert stats_result["embedding_coverage"] > 0
