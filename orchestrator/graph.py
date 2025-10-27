"""
LangGraph Workflow Definition

Defines the tutoring state machine with nodes and edges.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from orchestrator.state import TutoringState, GraphOutput
from orchestrator.nodes import (
    understanding_node,
    retrieval_node,
    planning_node,
    feedback_node,
    execution_node,
    evaluation_node,
    guide_node,
)


def route_after_understanding(state: TutoringState) -> Literal["retrieval", "execution", "guide"]:
    """
    Route to next node based on student intent.

    Returns:
        - "retrieval": Student has a question, need to fetch docs
        - "execution": Student wants to execute a command
        - "guide": Student wants next step
    """
    next_action = state.get("next_action", "retrieval")

    if next_action == "retrieve":
        return "retrieval"
    elif next_action == "execute":
        return "execution"
    elif next_action == "guide":
        return "guide"
    else:
        return "retrieval"  # Default


def route_after_retrieval(state: TutoringState) -> Literal["planning", "feedback"]:
    """
    After retrieval, decide whether to plan strategy or go straight to feedback.

    For complex questions, we plan the tutoring strategy first.
    For simple lookups, we can go straight to feedback.
    """
    # For now, always plan
    return "planning"


def route_after_planning(state: TutoringState) -> Literal["feedback"]:
    """
    After planning, always generate feedback.
    """
    return "feedback"


def route_after_execution(state: TutoringState) -> Literal["evaluation", "feedback"]:
    """
    After command execution, evaluate the result.
    """
    return "evaluation"


def route_after_evaluation(state: TutoringState) -> Literal["feedback"]:
    """
    After evaluation, provide feedback.
    """
    return "feedback"


def route_after_guide(state: TutoringState) -> Literal["feedback"]:
    """
    After guidance, provide feedback.
    """
    return "feedback"


def route_after_feedback(state: TutoringState) -> Literal["__end__"]:
    """
    After feedback, end the conversation turn.
    """
    return END


def create_tutoring_graph() -> StateGraph:
    """
    Create the LangGraph state machine for tutoring.

    Flow:
    1. Understanding: Parse student input
    2. [Conditional routing based on intent]
       - Question/Help → Retrieval → Planning → Feedback
       - Command → Execution → Evaluation → Feedback
       - Next Step → Guide → Feedback
    3. Feedback: Generate response → END
    """

    # Create graph
    graph = StateGraph(TutoringState)

    # Add nodes
    graph.add_node("understanding", understanding_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("planning", planning_node)
    graph.add_node("feedback", feedback_node)
    graph.add_node("execution", execution_node)
    graph.add_node("evaluation", evaluation_node)
    graph.add_node("guide", guide_node)

    # Set entry point
    graph.set_entry_point("understanding")

    # Add edges
    # From understanding, route based on intent
    graph.add_conditional_edges(
        "understanding",
        route_after_understanding,
        {
            "retrieval": "retrieval",
            "execution": "execution",
            "guide": "guide",
        }
    )

    # From retrieval, plan strategy
    graph.add_conditional_edges(
        "retrieval",
        route_after_retrieval,
        {
            "planning": "planning",
            "feedback": "feedback",
        }
    )

    # From planning, generate feedback
    graph.add_conditional_edges(
        "planning",
        route_after_planning,
        {
            "feedback": "feedback",
        }
    )

    # From execution, evaluate
    graph.add_conditional_edges(
        "execution",
        route_after_execution,
        {
            "evaluation": "evaluation",
            "feedback": "feedback",
        }
    )

    # From evaluation, feedback
    graph.add_conditional_edges(
        "evaluation",
        route_after_evaluation,
        {
            "feedback": "feedback",
        }
    )

    # From guide, feedback
    graph.add_conditional_edges(
        "guide",
        route_after_guide,
        {
            "feedback": "feedback",
        }
    )

    # From feedback, end
    graph.add_conditional_edges(
        "feedback",
        route_after_feedback,
        {
            END: END,
        }
    )

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
