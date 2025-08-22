# app/dash_assistant/slack/blocks.py
"""Slack blocks builder for dash assistant responses."""
from typing import Dict, List, Any
from app.config import logger


def build_slack_blocks(answer: Dict[str, Any], qid: int = None) -> List[Dict[str, Any]]:
    """Build Slack blocks from dash assistant answer.
    
    Args:
        answer: Answer dictionary from answer_builder
        qid: Query ID for feedback tracking
        
    Returns:
        List of Slack block kit blocks
    """
    logger.debug(f"Building Slack blocks for {len(answer.get('results', []))} results")
    
    blocks = []
    
    # Header block
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🔍 Найденные дашборды"
        }
    })
    
    results = answer.get('results', [])
    
    if not results:
        # No results found
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "❌ Дашборды не найдены. Попробуйте изменить запрос или использовать другие ключевые слова."
            }
        })
        return blocks
    
    # Process each result
    for i, result in enumerate(results):
        if i > 0:
            # Add divider between results
            blocks.append({"type": "divider"})
        
        # Result section
        result_section = _build_result_section(result, i + 1)
        blocks.append(result_section)
        
        # Action buttons for this result
        actions_block = _build_actions_block(result, qid)
        blocks.append(actions_block)
    
    # Add suggested filters if available
    suggested_filters = answer.get('suggested_filters', {})
    if suggested_filters:
        blocks.append({"type": "divider"})
        filters_block = _build_filters_section(suggested_filters)
        blocks.append(filters_block)
    
    logger.debug(f"Built {len(blocks)} Slack blocks")
    return blocks


def _build_result_section(result: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Build section block for a single result.
    
    Args:
        result: Single result from answer
        index: Result index (1-based)
        
    Returns:
        Slack section block
    """
    title = result.get('title', 'Untitled Dashboard')
    url = result.get('url', '')
    score = result.get('score', 0)
    why = result.get('why', 'Найдено по общему соответствию')
    charts = result.get('charts', [])
    
    # Truncate long titles
    if len(title) > 100:
        title = title[:97] + "..."
    
    # Build fields
    fields = []
    
    # Title and URL field
    title_text = f"*{index}. {_escape_slack_text(title)}*"
    if url:
        title_text += f"\n<{url}|Открыть дашборд>"
    fields.append({
        "type": "mrkdwn",
        "text": title_text
    })
    
    # Score and why field
    score_text = f"*Релевантность:* {score:.2f}\n*Почему найден:* {_escape_slack_text(why)}"
    fields.append({
        "type": "mrkdwn",
        "text": score_text
    })
    
    # Charts field (if any)
    if charts:
        charts_text = f"*Графики ({len(charts)}):*\n"
        for chart in charts[:3]:  # Limit to 3 charts
            chart_title = chart.get('title', 'Untitled Chart')
            chart_url = chart.get('url', '')
            
            if chart_url:
                charts_text += f"• <{chart_url}|{_escape_slack_text(chart_title)}>\n"
            else:
                charts_text += f"• {_escape_slack_text(chart_title)}\n"
        
        fields.append({
            "type": "mrkdwn",
            "text": charts_text.rstrip()
        })
    
    return {
        "type": "section",
        "fields": fields
    }


def _build_actions_block(result: Dict[str, Any], qid: int = None) -> Dict[str, Any]:
    """Build actions block with buttons for a result.
    
    Args:
        result: Single result from answer
        qid: Query ID for feedback tracking
        
    Returns:
        Slack actions block
    """
    import json
    url = result.get('url', '')
    entity_id = result.get('entity_id', 0)
    
    elements = []
    
    # "Открыть" button - URL buttons don't need action_id
    if url:
        elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Открыть"
            },
            "url": url,
            "style": "primary"
            # URL buttons should NOT have action_id
        })
    
    # Feedback buttons with unified action_id and JSON value
    elements.append({
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": "👍"
        },
        "value": json.dumps({"qid": qid, "vote": "up", "entity_id": entity_id}),
        "action_id": "feedback"
    })
    
    elements.append({
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": "👎"
        },
        "value": json.dumps({"qid": qid, "vote": "down", "entity_id": entity_id}),
        "action_id": "feedback"
    })
    
    return {
        "type": "actions",
        "block_id": f"fb_{qid}" if qid else "fb_0",
        "elements": elements
    }


def _build_filters_section(suggested_filters: Dict[str, Any]) -> Dict[str, Any]:
    """Build section for suggested filters.
    
    Args:
        suggested_filters: Dictionary of suggested filters
        
    Returns:
        Slack section block
    """
    filters_text = "*🔧 Рекомендуемые фильтры:*\n"
    
    for key, value in suggested_filters.items():
        # Format value based on type
        if isinstance(value, list):
            value_str = ", ".join(str(v) for v in value)
        else:
            value_str = str(value)
        
        filters_text += f"• `{key}`: {_escape_slack_text(value_str)}\n"
    
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": filters_text.rstrip()
        }
    }


def _escape_slack_text(text: str) -> str:
    """Escape special characters for Slack markdown.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for Slack
    """
    if not text:
        return ""
    
    # Escape special Slack markdown characters
    # Note: We're being conservative here to avoid breaking Slack formatting
    text = str(text)
    
    # Replace problematic characters that could break Slack formatting
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text


def build_slack_response_for_query(query: str, answer: Dict[str, Any], qid: int = None) -> Dict[str, Any]:
    """Build complete Slack response for a query.
    
    Args:
        query: Original user query
        answer: Answer from dash assistant
        qid: Query ID for feedback tracking
        
    Returns:
        Complete Slack response with blocks and metadata
    """
    blocks = build_slack_blocks(answer, qid)
    
    # Build response text (fallback for notifications)
    results_count = len(answer.get('results', []))
    if results_count == 0:
        response_text = f"По запросу '{query}' дашборды не найдены."
    else:
        response_text = f"По запросу '{query}' найдено {results_count} дашбордов."
    
    return {
        "response_type": "in_channel",  # Make response visible to all
        "text": response_text,
        "blocks": blocks
        # Note: metadata not supported in slash command responses
        # qid is embedded in button values instead
    }
