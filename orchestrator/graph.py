"""
LangGraph Workflow Definition

Defines the tutoring state machine with nodes and edges.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from orchestrator.state import TutoringState, GraphOutput
from orchestrator.nodes import (
    intent_router_node,
    retrieval_node,
    feedback_node,
    paraphrasing_node,
    teaching_retrieval_node,
    teaching_feedback_node,
)


def route_by_intent(state: TutoringState) -> Literal["teaching", "troubleshooting", "ambiguous"]:
    """
    Route to the appropriate path based on classified intent.

    Returns:
        - "teaching": Conceptual question path
        - "troubleshooting": Error/debugging path
        - "ambiguous": Ask for clarification
    """
    intent = state.get("intent", "teaching")
    return intent


def create_tutoring_graph() -> StateGraph:
    """
    Create the LangGraph state machine for tutoring.

    Two-Path Flow (Phase 2):

    Entry → Intent Router → Conditional Routing:

    1. Teaching Path (conceptual questions):
       - teaching_retrieval → teaching_feedback → END

    2. Troubleshooting Path (errors/debugging):
       - retrieval → feedback → paraphrasing → END
    """

    # Create graph
    graph = StateGraph(TutoringState)

    # Add intent router (entry point)
    graph.add_node("intent_router", intent_router_node)

    # Teaching path nodes
    graph.add_node("teaching_retrieval", teaching_retrieval_node)
    graph.add_node("teaching_feedback", teaching_feedback_node)

    # Troubleshooting path nodes (existing)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("feedback", feedback_node)
    graph.add_node("paraphrasing", paraphrasing_node)

    # Set entry point
    graph.set_entry_point("intent_router")

    # Conditional routing from intent_router
    graph.add_conditional_edges(
        "intent_router",
        route_by_intent,
        {
            "teaching": "teaching_retrieval",
            "troubleshooting": "retrieval",
            "ambiguous": "teaching_retrieval",  # Default to teaching for now
        }
    )

    # Teaching path edges
    graph.add_edge("teaching_retrieval", "teaching_feedback")
    graph.add_edge("teaching_feedback", END)

    # Troubleshooting path edges (unchanged)
    graph.add_edge("retrieval", "feedback")
    graph.add_edge("feedback", "paraphrasing")
    graph.add_edge("paraphrasing", END)

    return graph


def compile_graph():
    """
    Compile the graph for execution.
    """
    graph = create_tutoring_graph()
    return graph.compile()


# For debugging: visualize the graph
if __name__ == "__main__":
    try:
        from langchain_core.runnables.graph import CurveStyle, NodeStyles, MermaidDrawMethod

        graph = create_tutoring_graph()
        compiled = graph.compile()

        # Print Mermaid diagram
        print("LangGraph Tutoring Workflow:")
        print("=" * 60)
        print(compiled.get_graph().draw_mermaid())
        print("=" * 60)

    except ImportError:
        print("Install optional dependencies for visualization: pip install langchain-cli")
