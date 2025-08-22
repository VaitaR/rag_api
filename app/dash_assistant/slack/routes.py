import json
# app/dash_assistant/slack/routes.py
"""Slack integration routes for dash assistant."""
import hashlib
import hmac
import time
from typing import Dict, Any, Optional
from urllib.parse import parse_qs
from fastapi import APIRouter, HTTPException, Request, Form, status
from pydantic import BaseModel
import httpx

from app.config import logger, get_env_variable
from app.dash_assistant.db import DashAssistantDB
from app.dash_assistant.serving.retriever import DashRetriever
from app.dash_assistant.serving.answer_builder import build_answer
from .blocks import build_slack_response_for_query


# Slack configuration
SLACK_SIGNING_SECRET = get_env_variable("SLACK_SIGNING_SECRET", "test_secret_for_development")


# Router
router = APIRouter(prefix="/slack", tags=["slack-integration"])


def verify_slack_signature(raw_body: bytes, timestamp: str, signature: str) -> bool:
    """Verify Slack request signature using raw body."""
    if not SLACK_SIGNING_SECRET or SLACK_SIGNING_SECRET == "test_secret_for_development":
        # In development/test mode, skip signature verification
        logger.warning("Slack signature verification skipped (development mode)")
        return True
    
    # Check timestamp to prevent replay attacks
    if not timestamp:
        logger.warning("Missing timestamp in Slack request")
        return False
        
    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:  # 5 minutes
        logger.warning("Slack request timestamp too old")
        return False
    
    # Verify signature using raw body
    sig_basestring = f"v0:{timestamp}:{raw_body.decode()}"
    expected_signature = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


@router.post("/command")
async def handle_slash_command(request: Request):
    """Handle Slack slash command for dashboard search."""
    # Get raw body and headers for signature verification
    raw_body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "0")
    signature = request.headers.get("X-Slack-Signature", "")
    
    # Verify signature BEFORE parsing
    if not verify_slack_signature(raw_body, timestamp, signature):
        logger.warning("Invalid Slack signature")
        raise HTTPException(status_code=401, detail="Invalid Slack signature")
    
    # Parse form data from raw body
    form_data = parse_qs(raw_body.decode())
    text = (form_data.get("text") or [""])[0].strip()
    user_id = (form_data.get("user_id") or [""])[0]
    user_name = (form_data.get("user_name") or [""])[0]
    channel_id = (form_data.get("channel_id") or [""])[0]
    command = (form_data.get("command") or [""])[0]
    
    logger.info(f"Slack command received: {command} '{text}' from user {user_name}")
    
    # Check database health
    if not await DashAssistantDB.health_check():
        logger.error("Database health check failed")
        return {
            "response_type": "ephemeral",
            "text": "❌ Сервис временно недоступен. Попробуйте позже."
        }
    
    # Validate command
    if not text:
        return {
            "response_type": "ephemeral",
            "text": "❓ Пожалуйста, укажите поисковый запрос. Например: `/dash-search revenue analytics`"
        }
    
    try:
        # Log query to database
        qid = await _log_slack_query(user_id, user_name, text, channel_id)
        
        # Perform search
        retriever = DashRetriever()
        candidates = await retriever.search(query=text, top_k=5)
        
        # Build answer
        answer = build_answer(text, candidates)
        
        # Build Slack response with qid for feedback
        slack_response = build_slack_response_for_query(text, answer, qid)
        
        logger.info(f"Slack search completed: {len(answer['results'])} results for '{text}'")
        return slack_response
        
    except Exception as e:
        logger.error(f"Slack command processing failed: {e}")
        return {
            "response_type": "ephemeral",
            "text": f"❌ Произошла ошибка при поиске: {str(e)}"
        }


@router.post("/interactive")
async def handle_interactive_component(request: Request):
    """Handle Slack interactive components (button clicks)."""
    # Get raw body and headers for signature verification
    raw_body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "0")
    signature = request.headers.get("X-Slack-Signature", "")
    
    # Verify signature BEFORE parsing
    if not verify_slack_signature(raw_body, timestamp, signature):
        logger.warning("Invalid Slack signature for interactive component")
        raise HTTPException(status_code=401, detail="Invalid Slack signature")
    
    # Check for retries - don't duplicate side effects
    if request.headers.get("X-Slack-Retry-Num"):
        logger.info("Slack retry detected, returning empty response")
        return {}
    
    logger.info("Slack interactive component received")
    
    try:
        # Parse payload (Slack sends form-encoded JSON)
        form_data = parse_qs(raw_body.decode())
        payload_str = (form_data.get("payload") or [""])[0]
        
        if not payload_str:
            logger.error("No payload in interactive request")
            return {}
        
        payload = json.loads(payload_str)
        
        # Extract action information
        user = payload.get("user", {})
        actions = payload.get("actions", [])
        
        if not actions:
            logger.warning("No actions in payload")
            return {}
        
        action = actions[0]
        action_id = action.get("action_id", "")
        value = action.get("value", "")
        
        logger.info(f"Interactive action: {action_id} = {value} from user {user.get('id')}")
        
        # Process feedback action
        if action_id == "feedback":
            return await _process_feedback_action(payload, action, user)
        
        return {"text": "Действие обработано"}
        
    except Exception as e:
        logger.error(f"Interactive component processing failed: {e}")
        return {
            "text": "❌ Ошибка при обработке действия"
        }


async def _log_slack_query(user_id: str, user_name: str, query_text: str, channel_id: str) -> int:
    """Log Slack query to database."""
    try:
        qid = await DashAssistantDB.fetch_value("""
            INSERT INTO query_log (user_id, query_text, intent_json)
            VALUES ($1, $2, $3)
            RETURNING qid
        """, user_id, query_text, json.dumps({
            "source": "slack",
            "user_name": user_name,
            "channel_id": channel_id
        }))
        
        logger.debug(f"Logged Slack query: qid={qid}")
        return qid
        
    except Exception as e:
        logger.error(f"Failed to log Slack query: {e}")
        return -1


async def _process_feedback_action(payload: Dict[str, Any], action: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Process feedback action from Slack interactive component."""
    try:
        # Extract feedback data from action value (JSON)
        value_str = action.get("value", "{}")
        try:
            feedback_data = json.loads(value_str)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in action value: {value_str}")
            return {"text": "❌ Ошибка обработки feedback"}
        
        qid = feedback_data.get("qid")
        vote = feedback_data.get("vote")  # "up" or "down"
        
        logger.info(f"Feedback received: qid={qid}, vote={vote}, user={user.get('id')}")
        
        # Save feedback to database (simplified for now)
        # In full implementation, update query_log table with feedback
        
        # Update message blocks to show feedback was received
        blocks = payload.get("message", {}).get("blocks", []) or []
        
        # Find and update the actions block
        for block in blocks:
            if block.get("type") == "actions" and str(block.get("block_id", "")).startswith("fb_"):
                # Replace feedback buttons with confirmation
                feedback_text = "✅ Полезно" if vote == "up" else "❌ Не полезно"
                button_style = "primary" if vote == "up" else "danger"
                
                block["elements"] = [{
                    "type": "button",
                    "text": {"type": "plain_text", "text": feedback_text},
                    "style": button_style,
                    "action_id": "feedback_received"  # Disabled action
                }]
                break
        
        # Update message via response_url for reliable delivery
        response_url = payload.get("response_url")
        if response_url:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    update_response = await client.post(
                        response_url,
                        json={
                            "replace_original": True,
                            "blocks": blocks
                        }
                    )
                    logger.debug(f"Message updated via response_url: {update_response.status_code}")
            except Exception as e:
                logger.error(f"Failed to update message via response_url: {e}")
            
            # Return empty response since we updated via response_url
            return {}
        else:
            # Fallback: return updated blocks directly
            return {
                "replace_original": True,
                "blocks": blocks
            }
        
    except Exception as e:
        logger.error(f"Failed to process feedback action: {e}")
        return {"text": "❌ Ошибка при обработке feedback"}


@router.get("/health")
async def slack_health_check():
    """Health check for Slack integration."""
    return {
        "status": "healthy",
        "service": "slack-integration",
        "signing_secret_configured": bool(SLACK_SIGNING_SECRET and SLACK_SIGNING_SECRET != "test_secret_for_development")
    }
