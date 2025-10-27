"""
Tutoring State Definition

Defines the state structure for the LangGraph tutoring agent.
"""

from typing import List, Dict, Optional, TypedDict, Literal


class TutoringState(TypedDict):
    """
    Complete state for the tutoring conversation.

    This state flows through the entire LangGraph and is updated
    by each node in the state machine.
    """

    # ========================================
    # Student Interaction
    # ========================================
    student_question: str
    """Current question or input from student"""

    conversation_history: List[Dict[str, str]]
    """Full conversation history with role and content"""

    # ========================================
    # Lab Context
    # ========================================
    current_lab: str
    """Lab identifier (e.g., 'basic-routing', 'vlan-config')"""

    lab_step: int
    """Current step number in the lab exercise"""

    lab_objectives: List[str]
    """Learning objectives for this lab"""

    completed_objectives: List[str]
    """Objectives already mastered by student"""

    # ========================================
    # Retrieved Context (RAG)
    # ========================================
    retrieved_docs: List[str]
    """Relevant documentation chunks retrieved from FAISS"""

    relevant_concepts: List[str]
    """Related networking concepts"""

    retrieval_query: str
    """Query used for RAG retrieval"""

    # ========================================
    # Command Execution
    # ========================================
    command_to_execute: Optional[str]
    """Command to send to simulator"""

    execution_result: Optional[Dict]
    """Result from simulator execution"""

    expected_output: Optional[str]
    """Expected output for current step"""

    # ========================================
    # Simulator Integration (CLI Context)
    # ========================================
    cli_history: List[Dict[str, str]]
    """Transcript of CLI interactions from frontend
    Format: [{"command": "...", "output": "...", "timestamp": "...", "device_id": "..."}]
    """

    current_device_id: Optional[str]
    """Currently active device in simulator"""

    simulator_devices: Dict[str, Dict]
    """Created devices {device_id: {type, config, status}}"""

    ai_suggested_command: Optional[str]
    """Command suggested by AI for student to try"""

    ai_intervention_needed: bool
    """Flag indicating AI should provide guidance"""

    # ========================================
    # Tutoring Logic
    # ========================================
    student_intent: Literal["question", "command", "help", "next_step"]
    """Identified intent of student's input"""

    next_action: Literal["explain", "guide", "execute", "evaluate", "feedback"]
    """Next node to execute in state machine"""

    tutoring_strategy: Literal["socratic", "direct", "hint", "challenge"]
    """Pedagogical approach to use"""

    feedback_message: str
    """Generated feedback for student"""

    hints_given: int
    """Number of hints provided for current step"""

    max_hints: int
    """Maximum hints before providing solution"""

    # ========================================
    # Student Progress
    # ========================================
    mastery_level: Literal["novice", "intermediate", "advanced"]
    """Student's current skill level"""

    success_rate: float
    """Percentage of commands executed successfully"""

    concepts_understood: List[str]
    """Concepts student has demonstrated understanding of"""

    struggling_with: List[str]
    """Concepts student is having difficulty with"""

    # ========================================
    # Session Metadata
    # ========================================
    session_id: str
    """Unique identifier for this tutoring session"""

    start_time: str
    """ISO timestamp when session started"""

    total_interactions: int
    """Number of student inputs processed"""


class GraphOutput(TypedDict):
    """
    Final output structure returned to the user.
    """

    response: str
    """Message to display to student"""

    command_executed: Optional[str]
    """Command that was executed (if any)"""

    command_output: Optional[str]
    """Output from command execution (if any)"""

    next_suggestion: Optional[str]
    """Suggested next step for student"""

    progress: Dict
    """Progress indicators (% complete, objectives met, etc.)"""

    hints_remaining: int
    """How many more hints available"""
