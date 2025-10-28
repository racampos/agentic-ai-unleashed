"""
LangGraph Nodes for Tutoring Workflow

Each node represents a step in the tutoring state machine.
"""

from typing import Dict
import logging
from orchestrator.state import TutoringState
from orchestrator.rag_retriever import LabDocumentRetriever
from config.nim_config import get_llm_client, get_llm_config

logger = logging.getLogger(__name__)


# Initialize shared components
retriever = LabDocumentRetriever()
llm_client = get_llm_client()
llm_config = get_llm_config()


def understanding_node(state: TutoringState) -> Dict:
    """
    Parse student input and identify intent.

    Determines:
    - What is the student asking?
    - What type of help do they need?
    - What is their current context?

    Updates state:
    - student_intent: "question", "command", "help", "next_step"
    - next_action: Which node to execute next
    """
    student_question = state["student_question"]
    conversation_history = state["conversation_history"]
    current_lab = state["current_lab"]

    # Use LLM to classify intent
    prompt = f"""You are an AI tutor analyzing a student's input during a networking lab.

Current Lab: {current_lab}
Student Input: "{student_question}"

Analyze the student's intent. Choose ONE of the following:
- "question": Student is asking a conceptual question
- "command": Student wants to execute a command or is asking about commands
- "help": Student is stuck and needs guidance
- "next_step": Student wants to proceed to the next lab step

Respond with ONLY the intent category (one word).
"""

    response = llm_client.chat.completions.create(
        model=llm_config["model"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0.1,
    )

    intent = response.choices[0].message.content.strip().lower()

    # Validate intent
    valid_intents = ["question", "command", "help", "next_step"]
    if intent not in valid_intents:
        intent = "question"  # Default

    # Determine next action based on intent
    if intent in ["question", "help"]:
        next_action = "retrieve"  # Need to retrieve relevant documentation
    elif intent == "command":
        next_action = "execute"  # Execute command
    else:  # next_step
        next_action = "guide"  # Guide to next step

    return {
        "student_intent": intent,
        "next_action": next_action,
    }


def retrieval_node(state: TutoringState) -> Dict:
    """
    Query FAISS index to retrieve relevant documentation.

    Uses the student's question to find:
    - Relevant lab documentation
    - Related networking concepts
    - Example commands and explanations

    Updates state:
    - retrieved_docs: List of relevant documentation chunks
    - relevant_concepts: List of concept names
    """
    student_question = state["student_question"]
    current_lab = state["current_lab"]

    # Retrieve relevant documentation
    results = retriever.retrieve(
        query=student_question,
        k=5,
        filter_lab=current_lab if current_lab else None
    )

    # Extract content and metadata
    retrieved_docs = [result["content"] for result in results]
    relevant_concepts = []

    # Extract concepts from metadata if available
    for result in results:
        metadata = result.get("metadata", {})
        # Could extract concepts from section headings, etc.
        # For now, just store source info
        if "title" in metadata:
            relevant_concepts.append(metadata["title"])

    return {
        "retrieved_docs": retrieved_docs,
        "relevant_concepts": list(set(relevant_concepts)),  # Remove duplicates
        "retrieval_query": student_question,
        "next_action": "guide",  # After retrieval, generate guidance
    }


def planning_node(state: TutoringState) -> Dict:
    """
    Decide tutoring strategy based on student's mastery level.

    Analyzes:
    - Student's current understanding (mastery_level)
    - Number of hints already given
    - Success rate on commands
    - What concepts they're struggling with

    Updates state:
    - tutoring_strategy: "socratic", "direct", "hint", "challenge"
    - max_hints: Maximum hints to give before providing solution
    """
    mastery_level = state["mastery_level"]
    hints_given = state["hints_given"]
    max_hints = state["max_hints"]
    student_intent = state["student_intent"]

    # Choose strategy based on mastery level and intent
    if mastery_level == "novice":
        if hints_given >= max_hints:
            strategy = "direct"  # Give answer if max hints reached
        else:
            strategy = "socratic"  # Ask guiding questions
    elif mastery_level == "intermediate":
        if student_intent == "help":
            strategy = "hint"  # Provide hints
        else:
            strategy = "socratic"  # Encourage thinking
    else:  # advanced
        strategy = "challenge"  # Ask probing questions, extend concepts

    return {
        "tutoring_strategy": strategy,
    }


def feedback_node(state: TutoringState) -> Dict:
    """
    Generate personalized feedback for the student.

    Uses:
    - Retrieved documentation
    - Tutoring strategy
    - Student's question
    - Conversation history

    Generates:
    - Helpful, contextual response
    - Next steps or suggestions
    - Encouragement

    Updates state:
    - feedback_message: The response to show the student
    """
    student_question = state["student_question"]
    retrieved_docs = state.get("retrieved_docs", [])
    tutoring_strategy = state["tutoring_strategy"]
    mastery_level = state["mastery_level"]
    conversation_history = state["conversation_history"]
    student_intent = state["student_intent"]

    # CLI context (if available)
    cli_history = state.get("cli_history", [])
    ai_suggested_command = state.get("ai_suggested_command")
    ai_intervention_needed = state.get("ai_intervention_needed", False)

    # Build context from retrieved docs
    context = ""
    if retrieved_docs:
        context = "\n\nRelevant Documentation:\n" + "\n\n".join(retrieved_docs[:3])

    # Add CLI context if relevant
    cli_context = ""
    if cli_history:
        recent_cli = cli_history[-3:]  # Last 3 commands
        cli_context = "\n\nStudent's Recent Terminal Activity (you are observing their CLI session):\n" + "\n".join(
            f"Command executed: {entry.get('command', 'N/A')}\nOutput displayed: {entry.get('output', 'N/A')[:500]}"  # Increased from 200 to 500
            for entry in recent_cli
        )

    # Build system prompt based on tutoring strategy
    strategy_prompts = {
        "socratic": "Use the Socratic method. Ask guiding questions that help the student discover the answer themselves. Don't give direct answers.",
        "direct": "Provide a clear, direct explanation with step-by-step instructions.",
        "hint": "Provide a helpful hint that points the student in the right direction without giving away the complete answer.",
        "challenge": "Challenge the student with a thought-provoking question that extends their understanding beyond the basics.",
    }

    # Build enhanced system prompt with CLI context
    suggested_cmd_text = ""
    if ai_suggested_command:
        suggested_cmd_text = f"\n\nSuggested Command: {ai_suggested_command}\nYou may want to suggest this command to the student."

    system_prompt = f"""You are an expert networking tutor helping a student through a hands-on lab exercise.

Student Level: {mastery_level}
Tutoring Approach: {strategy_prompts.get(tutoring_strategy, strategy_prompts['socratic'])}

Student's Question: "{student_question}"
{context}
{cli_context}
{suggested_cmd_text}

Generate a helpful response that:
1. Addresses the student's question directly
2. If you can see relevant information in their terminal activity, reference what you observe (e.g., "I can see in your terminal..." or "Looking at your recent command output...")
3. Use the tutoring approach specified above, but prioritize being helpful and clear
4. If documentation is available, reference it when helpful
5. If a command is suggested, explain why it would be helpful
6. Encourage learning and exploration
7. Be concise (2-4 sentences for simple questions, 1-2 paragraphs for complex explanations)

IMPORTANT:
- You are observing their CLI session in real-time. Reference it as "I can see in your terminal..." not "the output you provided"
- When the student asks about information visible in their terminal, help them locate and interpret it
- Don't ask them to run commands they've already executed

Keep your tone friendly, encouraging, and educational.
"""

    # Generate response
    messages = [{"role": "system", "content": system_prompt}]

    # Add recent conversation history for context
    for msg in conversation_history[-4:]:  # Last 2 turns
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": student_question})

    # Log the full prompt for debugging
    logger.info(f"[LLM Prompt Debug] System prompt:\n{system_prompt}")
    logger.info(f"[LLM Prompt Debug] CLI context included: {bool(cli_context)}")
    logger.info(f"[LLM Prompt Debug] CLI history entries: {len(cli_history)}")

    response = llm_client.chat.completions.create(
        model=llm_config["model"],
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )

    feedback_message = response.choices[0].message.content.strip()

    # Update conversation history
    new_history = conversation_history + [
        {"role": "user", "content": student_question},
        {"role": "assistant", "content": feedback_message},
    ]

    return {
        "feedback_message": feedback_message,
        "conversation_history": new_history,
        "total_interactions": state["total_interactions"] + 1,
    }


def execution_node(state: TutoringState) -> Dict:
    """
    Execute a command on the network simulator.

    This node will:
    1. Parse the command from student's input
    2. Send it to NetGSim simulator
    3. Capture the output
    4. Store results for evaluation

    Updates state:
    - command_to_execute: The parsed command
    - execution_result: Simulator response
    - next_action: "evaluate" to assess the result

    TODO: Integrate with NetGSim API once available
    """
    student_question = state["student_question"]

    # For now, mock the execution
    # TODO: Replace with actual NetGSim API calls
    command_to_execute = extract_command_from_input(student_question)

    execution_result = {
        "success": True,
        "output": "Mock output - NetGSim integration pending",
        "command": command_to_execute,
    }

    return {
        "command_to_execute": command_to_execute,
        "execution_result": execution_result,
        "next_action": "evaluate",
    }


def evaluation_node(state: TutoringState) -> Dict:
    """
    Evaluate the result of a command execution.

    Checks:
    - Was the command successful?
    - Does the output match expected results?
    - Should we update student's mastery level?

    Updates state:
    - success_rate: Updated based on outcome
    - mastery_level: May upgrade if student is doing well
    - next_action: "feedback" to provide response

    TODO: Implement evaluation logic once NetGSim integration is complete
    """
    execution_result = state.get("execution_result")

    if not execution_result:
        return {"next_action": "feedback"}

    # TODO: Implement actual evaluation logic
    # For now, assume success
    success = execution_result.get("success", False)

    # Update success rate
    current_rate = state["success_rate"]
    total_interactions = state["total_interactions"]

    # Simple running average
    new_rate = (current_rate * total_interactions + (1.0 if success else 0.0)) / (total_interactions + 1)

    return {
        "success_rate": new_rate,
        "next_action": "feedback",
    }


def guide_node(state: TutoringState) -> Dict:
    """
    Guide student to the next step in their lab.

    Provides:
    - Overview of next objective
    - Hints about what to do
    - Links to relevant documentation

    Updates state:
    - lab_step: Incremented if moving forward
    - next_action: "feedback" to deliver guidance
    """
    current_step = state["lab_step"]
    lab_objectives = state["lab_objectives"]
    completed_objectives = state["completed_objectives"]

    # Check if current objective is complete
    if len(completed_objectives) < len(lab_objectives):
        next_objective = lab_objectives[len(completed_objectives)]

        # Retrieve documentation for next objective
        results = retriever.retrieve(
            query=next_objective,
            k=3,
            filter_lab=state.get("current_lab")
        )

        retrieved_docs = [result["content"] for result in results]

        return {
            "retrieved_docs": retrieved_docs,
            "next_action": "feedback",
        }
    else:
        # Lab complete!
        return {
            "feedback_message": "Congratulations! You've completed all objectives for this lab!",
            "next_action": "feedback",
        }


# Helper functions

def extract_command_from_input(text: str) -> str:
    """
    Extract a command from student's input.

    Looks for:
    - Text in code blocks
    - Commands starting with common CLI patterns
    - Explicit command indicators

    Returns:
        The extracted command, or the original text if no command found
    """
    # Simple extraction - look for code blocks
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            return parts[1].strip()

    # Look for common command patterns
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        # Cisco IOS commands often start with these
        if any(stripped.startswith(cmd) for cmd in ["show", "configure", "interface", "ip", "no", "exit"]):
            return stripped

    # Return original if no command found
    return text


def cli_analysis_node(state: TutoringState) -> Dict:
    """
    Analyze CLI interaction history to determine if AI intervention is needed.

    This node is called when the student executes a command in the browser CLI.
    It analyzes:
    - The command that was executed
    - The output received from the simulator
    - Recent CLI history (looking for patterns)
    - Whether student is stuck (repeated errors)
    - Whether command is potentially dangerous

    The AI can decide to:
    - Remain silent (student is doing fine)
    - Provide a warning (dangerous command)
    - Offer a hint (student seems stuck)
    - Suggest a better approach

    Updates state:
    - ai_intervention_needed: True if AI should respond
    - ai_suggested_command: Command to suggest (if any)
    - next_action: "feedback" if intervention needed, else end
    """
    cli_history = state.get("cli_history", [])
    current_device_id = state.get("current_device_id")
    lab_objectives = state.get("lab_objectives", [])
    completed_objectives = state.get("completed_objectives", [])

    # No history yet - nothing to analyze
    if not cli_history:
        logger.debug("No CLI history to analyze")
        return {
            "ai_intervention_needed": False,
            "next_action": "end",
        }

    # Get the most recent command
    latest_entry = cli_history[-1]
    latest_command = latest_entry.get("command", "")
    latest_output = latest_entry.get("output", "")

    # Analyze patterns in recent history (last 5 commands)
    recent_commands = [entry.get("command", "") for entry in cli_history[-5:]]
    recent_outputs = [entry.get("output", "") for entry in cli_history[-5:]]

    # Build analysis prompt
    analysis_prompt = f"""You are an AI networking tutor observing a student working on a lab exercise.

Current Device: {current_device_id or "Unknown"}
Lab Objectives: {', '.join(lab_objectives) if lab_objectives else "None specified"}
Completed: {', '.join(completed_objectives) if completed_objectives else "None yet"}

Recent Commands (last 5):
{chr(10).join(f"{i+1}. {cmd}" for i, cmd in enumerate(recent_commands))}

Latest Command: {latest_command}
Latest Output:
{latest_output[:500]}  # Truncate long output

Analyze the situation and decide if you should intervene. Consider:
1. Is the student making progress, or are they stuck (repeating similar commands)?
2. Did the command produce an error? Is it a learning opportunity?
3. Is the command potentially dangerous (e.g., shutting down wrong interface)?
4. Is the student on the right track toward lab objectives?

Respond with a JSON object:
{{
  "should_intervene": true/false,
  "reason": "brief explanation",
  "suggested_command": "optional command to suggest",
  "message_tone": "silent/hint/warning/encouragement"
}}

If should_intervene is false, the AI will remain silent.
"""

    # Use LLM to analyze
    response = llm_client.chat.completions.create(
        model=llm_config["model"],
        messages=[{"role": "user", "content": analysis_prompt}],
        max_tokens=200,
        temperature=0.3,
    )

    analysis_text = response.choices[0].message.content.strip()

    # Parse JSON response (simple parsing - could use json.loads in production)
    should_intervene = "true" in analysis_text.lower() and "should_intervene" in analysis_text.lower()

    # Extract suggested command if present
    suggested_command = None
    if "suggested_command" in analysis_text:
        # Simple extraction - in production, use proper JSON parsing
        try:
            import json
            analysis_json = json.loads(analysis_text)
            suggested_command = analysis_json.get("suggested_command")
            should_intervene = analysis_json.get("should_intervene", False)
        except:
            # Fallback if JSON parsing fails
            pass

    logger.info(f"CLI analysis: should_intervene={should_intervene}, latest_command={latest_command}")

    if should_intervene:
        # Store the analysis for feedback node to use
        return {
            "ai_intervention_needed": True,
            "ai_suggested_command": suggested_command,
            "retrieval_query": f"help with command: {latest_command}",
            "next_action": "retrieve",  # Retrieve docs, then give feedback
        }
    else:
        # Student is doing fine, no intervention needed
        return {
            "ai_intervention_needed": False,
            "next_action": "end",
        }


def device_management_node(state: TutoringState) -> Dict:
    """
    Manage simulator devices based on lab requirements.

    This node is called when:
    - Lab starts and devices need to be created
    - Student needs a specific device type
    - Topology needs to be set up

    This is a placeholder for now - actual device creation will be
    handled by the FastAPI endpoints calling the NetGSimClient.

    Updates state:
    - simulator_devices: Updated device registry
    - current_device_id: Set to newly created device
    """
    current_lab = state.get("current_lab")
    simulator_devices = state.get("simulator_devices", {})

    # For now, just log that device management was requested
    logger.info(f"Device management requested for lab: {current_lab}")
    logger.info(f"Current devices: {list(simulator_devices.keys())}")

    # In actual implementation, this would:
    # 1. Determine what devices are needed for the lab
    # 2. Create them via NetGSimClient
    # 3. Update the state with device info

    return {
        "next_action": "feedback",
    }
