"""
LangGraph Workflow Definition

Defines the tutoring state machine with nodes and edges.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from orchestrator.state import TutoringState, GraphOutput
from orchestrator.nodes import (
    retrieval_node,
    feedback_node,
    paraphrasing_node,
)


def create_tutoring_graph() -> StateGraph:
    """
    Create the LangGraph state machine for tutoring.

    Simplified Flow (Phase 1):
    1. Retrieval: Fetch relevant documentation via RAG
    2. Feedback: Generate response with error context and RAG
    3. Paraphrasing: Clean up response (remove tool references)
    4. END
    """

    # Create graph
    graph = StateGraph(TutoringState)

    # Add nodes
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("feedback", feedback_node)
    graph.add_node("paraphrasing", paraphrasing_node)

    # Set entry point
    graph.set_entry_point("retrieval")

    # Add edges (simple linear flow)
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
