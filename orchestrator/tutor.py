"""
AI Networking Lab Tutor

Main interface for interacting with the tutoring agent.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict
from orchestrator.state import TutoringState, GraphOutput
from orchestrator.graph import compile_graph


class NetworkingLabTutor:
    """
    Main tutoring agent that guides students through networking labs.

    Usage:
        tutor = NetworkingLabTutor()
        tutor.start_lab("01-basic-routing")
        response = tutor.ask("How do I configure an IP address?")
        print(response["response"])
    """

    def __init__(self):
        """Initialize the tutoring agent."""
        self.graph = compile_graph()
        self.session_id = str(uuid.uuid4())
        self.state: Optional[TutoringState] = None

    def start_lab(
        self,
        lab_id: str,
        lab_title: str = "",
        lab_description: str = "",
        lab_instructions: str = "",
        lab_objectives: list = None,
        lab_topology_info: Dict = None,
        mastery_level: str = "novice"
    ) -> Dict:
        """
        Start a new lab session with full lab context.

        Args:
            lab_id: Lab identifier (e.g., "01-basic-routing")
            lab_title: Human-readable lab title
            lab_description: Brief lab description
            lab_instructions: Full lab instructions from markdown
            lab_objectives: List of learning objectives (parsed from lab content)
            lab_topology_info: Information about network topology
            mastery_level: Student's skill level ("novice", "intermediate", "advanced")

        Returns:
            Welcome message and lab info
        """
        # Use provided objectives or fall back to hardcoded ones
        if not lab_objectives:
            lab_objectives = self._get_lab_objectives(lab_id)

        # Initialize state for new lab
        self.state = TutoringState(
            # Student interaction
            student_question="",
            conversation_history=[],

            # Lab context
            current_lab=lab_id,
            lab_title=lab_title or lab_id,
            lab_description=lab_description,
            lab_instructions=lab_instructions,
            lab_step=1,
            lab_objectives=lab_objectives,
            completed_objectives=[],
            lab_topology_info=lab_topology_info,

            # Retrieved context
            retrieved_docs=[],
            relevant_concepts=[],
            retrieval_query="",

            # Command execution
            command_to_execute=None,
            execution_result=None,
            expected_output=None,

            # Simulator integration (CLI Context)
            cli_history=[],
            current_device_id=None,
            simulator_devices={},
            ai_suggested_command=None,
            ai_intervention_needed=False,

            # Tutoring logic
            student_intent="question",
            next_action="explain",
            tutoring_strategy="socratic",
            feedback_message="",
            hints_given=0,
            max_hints=3,

            # Student progress
            mastery_level=mastery_level,
            success_rate=0.0,
            concepts_understood=[],
            struggling_with=[],

            # Session metadata
            session_id=self.session_id,
            start_time=datetime.utcnow().isoformat(),
            total_interactions=0,
        )

        welcome_message = f"""Welcome to the AI Networking Lab Tutor!

Lab: {lab_id}
Skill Level: {mastery_level}

Objectives for this lab:
"""
        for i, obj in enumerate(self.state["lab_objectives"], 1):
            welcome_message += f"{i}. {obj}\n"

        welcome_message += """
I'm here to help you through this lab! You can:
- Ask questions about concepts
- Request help with commands
- Ask for hints when stuck
- Request the next step

Let's get started! What would you like to know?
"""

        return {
            "response": welcome_message,
            "lab_id": lab_id,
            "session_id": self.session_id,
        }

    def ask(self, question: str) -> GraphOutput:
        """
        Ask the tutor a question or request help.

        Args:
            question: Student's question or input

        Returns:
            GraphOutput with response and metadata
        """
        if not self.state:
            return {
                "response": "Please start a lab first using start_lab(lab_id)",
                "command_executed": None,
                "command_output": None,
                "next_suggestion": None,
                "progress": {},
                "hints_remaining": 0,
            }

        # Update state with new question
        self.state["student_question"] = question

        # Run the graph
        result = self.graph.invoke(self.state)

        # Update internal state
        self.state = result

        # Build output
        output: GraphOutput = {
            "response": result["feedback_message"],
            "command_executed": result.get("command_to_execute"),
            "command_output": (
                result["execution_result"].get("output")
                if result.get("execution_result")
                else None
            ),
            "next_suggestion": self._get_next_suggestion(result),
            "progress": {
                "objectives_completed": len(result["completed_objectives"]),
                "total_objectives": len(result["lab_objectives"]),
                "success_rate": round(result["success_rate"] * 100, 1),
                "mastery_level": result["mastery_level"],
            },
            "hints_remaining": result["max_hints"] - result["hints_given"],
        }

        return output

    def get_progress(self) -> Dict:
        """
        Get current progress in the lab.

        Returns:
            Progress information
        """
        if not self.state:
            return {"error": "No active lab session"}

        return {
            "lab_id": self.state["current_lab"],
            "lab_step": self.state["lab_step"],
            "objectives_completed": len(self.state["completed_objectives"]),
            "total_objectives": len(self.state["lab_objectives"]),
            "success_rate": round(self.state["success_rate"] * 100, 1),
            "mastery_level": self.state["mastery_level"],
            "concepts_understood": self.state["concepts_understood"],
            "struggling_with": self.state["struggling_with"],
            "total_interactions": self.state["total_interactions"],
        }

    def _get_lab_objectives(self, lab_id: str) -> list:
        """
        Get objectives for a lab.

        TODO: Load from lab metadata or documentation
        """
        objectives_map = {
            "01-basic-routing": [
                "Access router and enter privileged mode",
                "Configure hostname and passwords",
                "Configure IP addresses on interfaces",
                "Verify interface status",
                "Test connectivity with ping",
            ],
            "02-static-routing": [
                "Understand routing fundamentals",
                "Configure static routes",
                "Verify routing table entries",
                "Test end-to-end connectivity",
                "Configure default routes",
            ],
        }

        return objectives_map.get(lab_id, ["Complete the lab exercises"])

    def _get_next_suggestion(self, state: TutoringState) -> Optional[str]:
        """
        Generate a suggestion for what to do next.

        Args:
            state: Current tutoring state

        Returns:
            Suggestion text or None
        """
        completed = len(state["completed_objectives"])
        total = len(state["lab_objectives"])

        if completed < total:
            next_objective = state["lab_objectives"][completed]
            return f"Next objective: {next_objective}"
        else:
            return "Lab complete! Great work!"


def main():
    """
    Demo the tutoring agent.
    """
    print("=" * 60)
    print("AI Networking Lab Tutor - Demo")
    print("=" * 60)

    # Create tutor
    tutor = NetworkingLabTutor()

    # Start a lab
    welcome = tutor.start_lab("01-basic-routing", mastery_level="novice")
    print("\n" + welcome["response"])

    # Simulate some questions
    questions = [
        "How do I configure an IP address on a router interface?",
        "What does 'no shutdown' do?",
        "I want to see the next step",
    ]

    for question in questions:
        print("\n" + "=" * 60)
        print(f"Student: {question}")
        print("=" * 60)

        response = tutor.ask(question)

        print(f"\nTutor: {response['response']}")

        if response.get("next_suggestion"):
            print(f"\nNext: {response['next_suggestion']}")

        print(f"\nProgress: {response['progress']['objectives_completed']}/{response['progress']['total_objectives']} objectives")
        print(f"Hints remaining: {response['hints_remaining']}")


if __name__ == "__main__":
    main()
