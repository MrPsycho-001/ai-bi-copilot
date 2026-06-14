import json
import google.generativeai as genai
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from app.core.config import settings
from app.services.analyzer import LocalDataAnalyzer

genai.configure(api_key=settings.GEMINI_API_KEY)

# Added chat_history to the state definition
class AgentState(TypedDict):
    user_query: str
    chat_history: list
    dataset_path: str
    schema_metadata: dict
    extracted_metrics: dict
    final_response: str
    next_step: str

def schema_inspector_node(state: AgentState) -> Dict[str, Any]:
    query = state["user_query"].lower()
    # We added "them" and "these" as keywords to catch follow-up pronoun questions!
    analytical_keywords = [
        "summary", "stats", "profile", "mean", "median", "average", "distribution",
        "highest", "lowest", "max", "min", "top", "bottom", "total", "column", 
        "find", "who", "show", "give", "chart", "graph", "plot", "they", "them", "these"
    ]
    if any(keyword in query for keyword in analytical_keywords):
        return {"next_step": "run_analytics"}
    return {"next_step": "direct_respond"}

def analytical_execution_node(state: AgentState) -> Dict[str, Any]:
    try:
        analyzer = LocalDataAnalyzer(state["dataset_path"])
        profile_summary = analyzer.generate_summary_profile()
        return {"extracted_metrics": profile_summary, "next_step": "finalize"}
    except Exception as e:
        return {"extracted_metrics": {"error": str(e)}, "next_step": "finalize"}

def gemini_synthesis_node(state: AgentState) -> Dict[str, Any]:
    # We format the last 4 messages so Gemini knows the exact context of pronouns
    history_context = json.dumps(state.get("chat_history", [])[-4:], indent=2)

    prompt = f"""
    You are an expert enterprise Business Intelligence Copilot.
    
    RECENT CONVERSATION HISTORY (Use this for context if the user asks a follow-up question):
    {history_context}
    
    CURRENT QUESTION: '{state["user_query"]}'
    
    Dataset Schema:
    {json.dumps(state["schema_metadata"])}
    
    Data Metrics:
    {json.dumps(state.get("extracted_metrics", {}))}
    
    INSTRUCTIONS:
    1. Analyze the data and answer the current question, using the history for context if they say "them" or "they".
    2. You MUST return your response as a JSON object.
    3. The JSON must contain exactly two keys:
       - "text_answer": A string with your detailed, natural language response.
       - "chart_data": An array of objects for visualization. E.g., [{{"name": "A", "value": 10}}]. Or [] if no chart is needed.
    """
    
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
    
    try:
        response = model.generate_content(prompt)
        return {"final_response": response.text}
    except Exception as e:
        fallback = {"text_answer": f"Error: {str(e)}", "chart_data": []}
        return {"final_response": json.dumps(fallback)}

def router_decision_edge(state: AgentState) -> str:
    return state["next_step"]

workflow = StateGraph(AgentState)
workflow.add_node("inspector", schema_inspector_node)
workflow.add_node("analyzer_engine", analytical_execution_node)
workflow.add_node("synthesis_brain", gemini_synthesis_node)
workflow.set_entry_point("inspector")
workflow.add_conditional_edges("inspector", router_decision_edge, {"run_analytics": "analyzer_engine", "direct_respond": "synthesis_brain"})
workflow.add_edge("analyzer_engine", "synthesis_brain")
workflow.add_edge("synthesis_brain", END)

bi_agent_executor = workflow.compile()
