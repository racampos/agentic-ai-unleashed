"""
LangGraph Nodes for Tutoring Workflow

Each node represents a step in the tutoring state machine.
"""

from typing import Dict
import logging
import json
from orchestrator.state import TutoringState
from orchestrator.rag_retriever import LabDocumentRetriever
from orchestrator import tools
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
    lab_title = state.get("lab_title", current_lab)

    # Use LLM to classify intent
    prompt = f"""You are an AI tutor analyzing a student's input during a networking lab.

Current Lab: {lab_title}
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


async def feedback_node(state: TutoringState) -> Dict:
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

    # Lab context
    lab_title = state.get("lab_title", state.get("current_lab", ""))
    lab_description = state.get("lab_description", "")
    lab_instructions = state.get("lab_instructions", "")
    lab_objectives = state.get("lab_objectives", [])
    lab_topology_info = state.get("lab_topology_info")

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

    # Build lab context section
    lab_context = f"\n\nLab: {lab_title}"
    if lab_description:
        lab_context += f"\nDescription: {lab_description}"

    if lab_objectives:
        lab_context += "\n\nLab Objectives:"
        for i, obj in enumerate(lab_objectives, 1):
            lab_context += f"\n  {i}. {obj}"

    if lab_topology_info:
        device_count = lab_topology_info.get("device_count", 0)
        connection_count = lab_topology_info.get("connection_count", 0)
        lab_context += f"\n\nLab Topology: {device_count} devices, {connection_count} connections"

        # Add device names if available
        devices = lab_topology_info.get("devices", [])
        if devices:
            device_names = [d.get("name", d.get("device_id", "?")) for d in devices[:5]]  # Show first 5
            lab_context += f"\nDevices: {', '.join(device_names)}"
            if len(devices) > 5:
                lab_context += f" (and {len(devices) - 5} more)"

    # Add lab instructions (including addressing tables and requirements)
    if lab_instructions:
        # Include more of the instructions to ensure addressing tables are included
        # Most labs are 2000-5000 chars, which is reasonable for context
        max_instruction_length = 5000
        instructions_preview = lab_instructions[:max_instruction_length].strip()
        if len(lab_instructions) > max_instruction_length:
            instructions_preview += "\n... [additional content truncated]"
        lab_context += f"\n\nLab Scenario/Requirements (including addressing tables):\n{instructions_preview}"

    # Build enhanced system prompt with CLI context
    suggested_cmd_text = ""
    if ai_suggested_command:
        suggested_cmd_text = f"\n\nSuggested Command: {ai_suggested_command}\nYou may want to suggest this command to the student."

    system_prompt = f"""You are a highly experienced Cisco-certified networking instructor with deep expertise in router and switch configuration.

IMPORTANT - Your Communication Style:
- Speak with authority and confidence about networking concepts
- Use precise technical terminology without hedging language
- When you know something definitively (like what 'enable' or 'configure terminal' means), state it with confidence
- Example: "The 'enable' command grants privileged EXEC mode access" NOT "I believe 'enable' is for accessing privileged mode"
- Only express uncertainty when information is truly ambiguous or unknown

Student Level: {mastery_level}
Tutoring Approach: {strategy_prompts.get(tutoring_strategy, strategy_prompts['socratic'])}
{lab_context}

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
- You have a tool to retrieve device running configurations. When asked about device configuration (IP addresses, routing, VLANs, etc.), use the get_device_running_config tool to fetch the current configuration. After retrieving it, reference it as "Based on the device's running configuration..." or "I checked the running configuration and..."
- When the student asks about information visible in their terminal, help them locate and interpret it
- Don't ask them to run commands they've already executed

Keep your tone friendly, encouraging, and educational.
"""

    # Generate response with reasoning mode enabled
    # Prepend "detailed thinking on" to activate reasoning mode
    # Note: The <think> tags may not be visible in responses, but the reasoning
    # quality improvement is still present based on testing
    system_prompt_with_reasoning = f"detailed thinking on\n\n{system_prompt}"
    messages = [
        {"role": "system", "content": system_prompt_with_reasoning}
    ]

    # Add recent conversation history for context
    for msg in conversation_history[-4:]:  # Last 2 turns
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": student_question})

    # Call LLM with tool support
    # May require multiple iterations if the LLM calls tools
    max_tool_iterations = 3
    for iteration in range(max_tool_iterations):
        logger.info(f"[Tool Calling] Iteration {iteration + 1}/{max_tool_iterations}")

        # Call LLM with reasoning mode enabled and tool support
        response = llm_client.chat.completions.create(
            model=llm_config["model"],
            messages=messages,
            tools=tools.TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=2048,  # Increased to allow for reasoning output
            temperature=0.6,  # Recommended for reasoning mode
            top_p=0.95,       # Recommended for reasoning mode
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # If no tool calls, we're done
        if not tool_calls:
            feedback_message = response_message.content.strip() if response_message.content else ""
            break

        # Add the assistant's response with tool calls to messages
        messages.append(response_message)

        # Execute each tool call
        logger.info(f"[Tool Calling] LLM requested {len(tool_calls)} tool call(s)")
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            logger.info(f"[Tool Calling] Executing tool: {function_name} with args: {function_args}")

            # Get the tool implementation
            tool_impl = tools.TOOL_IMPLEMENTATIONS.get(function_name)
            if not tool_impl:
                tool_result = f"Error: Unknown tool '{function_name}'"
            else:
                # Execute the tool (async)
                try:
                    tool_result = await tool_impl(**function_args)
                    logger.info(f"[Tool Calling] Tool {function_name} returned {len(str(tool_result))} chars")
                except Exception as e:
                    tool_result = f"Error executing tool: {str(e)}"
                    logger.error(f"[Tool Calling] Tool execution error: {e}")

            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": str(tool_result),
            })

        # Loop will call LLM again with tool results
    else:
        # Max iterations reached
        feedback_message = "I apologize, but I'm having trouble processing your request. Please try rephrasing your question."
        logger.warning("[Tool Calling] Max tool iterations reached")

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

async def feedback_node_stream(state: TutoringState):
    """
    Streaming version of feedback_node that yields response chunks in real-time.

    Yields:
        Dictionary chunks with 'type' and content
    """
    # Prepare the same prompt as feedback_node
    student_question = state["student_question"]
    tutoring_strategy = state["tutoring_strategy"]
    conversation_history = state["conversation_history"]
    cli_history = state.get("cli_history", [])

    print("\n" + "=" * 80, flush=True)
    print("[DEBUG] feedback_node_stream called!", flush=True)
    print(f"[DEBUG] Student question: {student_question}", flush=True)
    print(f"[DEBUG] CLI history entries: {len(cli_history)}", flush=True)
    print("=" * 80 + "\n", flush=True)

    logger.info("=" * 80)
    logger.info("[FEEDBACK_NODE_STREAM] Starting new interaction")
    logger.info(f"[FEEDBACK_NODE_STREAM] Student question: {student_question}")
    logger.info(f"[FEEDBACK_NODE_STREAM] CLI history entries: {len(cli_history)}")
    
    # Build CLI context
    cli_context = ""
    if cli_history:
        recent_commands = cli_history[-5:]  # Last 5 commands
        cli_context = "\n\n=== STUDENT'S TERMINAL ACTIVITY (CRITICAL - READ THIS FIRST) ===\n"
        cli_context += "You are observing their actual CLI session. Pay SPECIAL ATTENTION to:\n"
        cli_context += "- The PROMPT shows the current mode (Router#=privileged exec, Router(config)#=global config, Router(config-if)#=interface config)\n"
        cli_context += "- Commands that produced ERROR messages (% Invalid input, % Incomplete command, etc.)\n"
        cli_context += "- The EXACT syntax they used (this is what you need to correct)\n"
        cli_context += "- The ^ marker shows WHERE the error occurred\n"
        cli_context += "- Common mistake: Running interface commands like 'ip address' in global config mode instead of interface config mode\n\n"
        for cmd_entry in recent_commands:
            cmd = cmd_entry.get("command", "")
            output = cmd_entry.get("output", "")
            cli_context += f">>> Student typed: {cmd}\n"
            cli_context += f"<<< Router response:\n{output[:500]}\n"

            # Detect specific common errors
            if "Invalid input" in output or "Incomplete command" in output or "%" in output:
                cli_context += "⚠️ THIS COMMAND FAILED - Your job is to explain what's wrong and provide the CORRECT syntax\n"

                # Check for CIDR notation error (e.g., /24 instead of 255.255.255.0)
                if "/24" in cmd or "/25" in cmd or "/26" in cmd or "/27" in cmd or "/28" in cmd or "/29" in cmd or "/30" in cmd:
                    cli_context += "⚠️ DETECTED: Student used CIDR notation (like /24) which Cisco IOS does NOT support. They need subnet mask format (like 255.255.255.0)\n"

            cli_context += "\n"

    print(f"[DEBUG] CLI context length: {len(cli_context)} chars", flush=True)
    if cli_context:
        print(f"[DEBUG] CLI context preview:\n{cli_context[:500]}\n...", flush=True)

    logger.info("[FEEDBACK_NODE_STREAM] CLI context built:")
    logger.info(cli_context[:1000] + ("..." if len(cli_context) > 1000 else ""))

    # Perform RAG retrieval for grounding
    # Enhance query with CLI context for better retrieval
    retrieval_query = student_question
    if cli_history:
        # Extract keywords from failed commands to improve retrieval
        command_keywords = []
        for cmd_entry in cli_history[-5:]:
            cmd = cmd_entry.get("command", "")
            output = cmd_entry.get("output", "")
            if "Invalid input" in output or "%" in output:
                # Extract command name (first word) for better semantic matching
                cmd_parts = cmd.strip().split()
                if cmd_parts:
                    # Add command keywords like "ip address", "hostname", etc.
                    if len(cmd_parts) >= 2:
                        command_keywords.append(f"{cmd_parts[0]} {cmd_parts[1]}")
                    else:
                        command_keywords.append(cmd_parts[0])

        if command_keywords:
            # Enhance query with command keywords
            retrieval_query = f"Cisco IOS {' '.join(command_keywords)} command syntax"
            print(f"[DEBUG] Enhanced retrieval query: {retrieval_query}", flush=True)
        else:
            # Fallback: add "Cisco IOS" to make it more specific
            retrieval_query = f"Cisco IOS {student_question}"
            print(f"[DEBUG] Fallback retrieval query: {retrieval_query}", flush=True)

    # Perform RAG retrieval with a two-stage strategy:
    # 1. Get cisco-ios-command-reference.md chunks (no lab filter)
    # 2. Get lab-specific context (with lab filter)
    retrieved_docs = []
    command_ref_chunks = []
    lab_specific_chunks = []

    try:
        # Stage 1: Always retrieve from cisco-ios-command-reference.md (highest priority)
        print(f"[DEBUG] RAG Query: {retrieval_query}", flush=True)

        # Get top command reference chunks without lab filter
        all_results = retriever.retrieve(
            query=retrieval_query,
            k=10,  # Get more results to sort through
            filter_lab=None  # Don't filter - we want command reference!
        )

        # Separate command reference chunks from other chunks
        for result in all_results:
            if result["metadata"]["lab_id"] == "cisco-ios-command-reference":
                command_ref_chunks.append(result)
            elif state.get("current_lab") and result["metadata"]["lab_id"] == state.get("current_lab"):
                lab_specific_chunks.append(result)

        print(f"[DEBUG] Found {len(command_ref_chunks)} cisco-ios-command-reference chunks", flush=True)
        print(f"[DEBUG] Found {len(lab_specific_chunks)} lab-specific chunks", flush=True)

        # Build final retrieved docs: prioritize command reference, then lab-specific
        # Take top 2-3 command ref chunks (most relevant)
        retrieved_docs = command_ref_chunks[:3]

        # Add 1-2 lab-specific chunks if available and we have room
        if lab_specific_chunks and len(retrieved_docs) < 4:
            retrieved_docs.extend(lab_specific_chunks[:2])

        print(f"[DEBUG] Final RAG results: {len(retrieved_docs)} documents", flush=True)
        for i, result in enumerate(retrieved_docs, 1):
            print(f"[DEBUG] Doc {i} (score: {result['score']:.4f}): {result['metadata']['lab_id']} - {result['content'][:150]}...", flush=True)

        logger.info(f"[FEEDBACK_NODE_STREAM] RAG retrieved {len(retrieved_docs)} documents")

    except Exception as e:
        print(f"[DEBUG] RAG retrieval failed: {e}", flush=True)
        logger.warning(f"RAG retrieval failed: {e}")

    # Build documentation context from RAG results
    doc_context = "\n\nRELEVANT DOCUMENTATION (Use this as your source of truth):\n"

    if retrieved_docs:
        for i, result in enumerate(retrieved_docs, 1):
            doc_type = "CISCO IOS COMMAND REFERENCE" if result["metadata"]["lab_id"] == "cisco-ios-command-reference" else "LAB CONTEXT"
            doc_context += f"\n[{doc_type} - Doc {i}]:\n{result['content']}\n"

    # Build enhanced system prompt with anti-hallucination instructions
    system_prompt = f"""You are a Cisco IOS networking tutor. Your PRIMARY DUTY is to provide accurate, concise answers grounded ONLY in the documentation provided.

Student Level: {state["mastery_level"]}

Student's Question: "{student_question}"

{cli_context}

CRITICAL: The STUDENT'S TERMINAL ACTIVITY above shows their ACTUAL router session. This is your PRIMARY source of truth.
- If you see a prompt like "Floor14(config-if)#", they ARE in interface config mode
- If you see an error with ^, that's where the syntax is wrong
- DO NOT contradict what's visible in their terminal!

{doc_context}

RESPONSE RULES (MANDATORY):

1. **LENGTH AND CLARITY:**
   - For SIMPLE questions (single command, definition): Answer in 1-2 sentences maximum
   - For COMPLEX questions (multi-step processes): Answer in 3-5 sentences maximum
   - Get straight to the point. NO rambling or tangential information
   - Example: "How do I change the hostname?" → "Use `hostname [name]` in global config mode. Example: `hostname Router1`. No reboot required."

2. **INFORMATION SOURCE (STRICT):**
   - ONLY use information from "RELEVANT DOCUMENTATION" section above
   - If documentation doesn't have the answer, say: "I don't see that in the provided documentation"
   - NEVER mention other operating systems (Linux, Windows, etc.) unless explicitly asked
   - NEVER mention files like /etc/hosts, /etc/hostname unless they appear in the Cisco documentation
   - DO NOT add general networking knowledge unless directly asked

3. **COMMAND ACCURACY:**
   - Copy command syntax EXACTLY as shown in documentation
   - If command is not in documentation, DO NOT suggest it
   - NEVER paraphrase or modify documented commands
   - Include concrete example from docs when available

3a. **CRITICAL: IP ADDRESS COMMAND SYNTAX:**
   ✅ CORRECT: `ip address 192.168.1.1 255.255.255.0` (address space mask)
   ❌ WRONG: `ip address 192.168.1.1/24` (CIDR notation - NOT SUPPORTED in Cisco IOS)
   ❌ WRONG: `ip address 192.168.1.1 24` (prefix length - NOT SUPPORTED)
   - Cisco IOS requires FULL SUBNET MASK (255.255.255.0), NOT CIDR notation (/24)
   - This is the #1 most common mistake - always use dotted decimal mask

4. **PROHIBITED BEHAVIORS:**
   ❌ NEVER say "typically located at /etc/hosts or /etc/hostname"
   ❌ NEVER mention rebooting unless documentation explicitly requires it
   ❌ NEVER suggest commands not present in the RELEVANT DOCUMENTATION section
   ❌ NEVER add verbose explanations for simple commands
   ❌ NEVER discuss other operating systems unless specifically asked

5. **REQUIRED FORMAT:**
   - Start with the direct answer (command or concept)
   - Include example from documentation if available
   - Stop. Do not add unnecessary context.

6. **TOOL USE (IMPORTANT):**
   - You have access to `get_device_running_config(device_name)` to retrieve live device configurations
   - ONLY use this tool when:
     * Student asks "What IP address is configured?" or "Show me the current config"
     * Student asks "What's the current state of device X?" or "Is interface X up/down?"
     * You need to verify configuration that is NOT visible in their terminal history
   - DO NOT use tools when:
     * Student has ERROR messages visible in their terminal (analyze the error instead!)
     * Student is asking about command syntax or "how do I..."
     * The answer is in the RELEVANT DOCUMENTATION or CLI history
   - PRIORITIZE: CLI history > Documentation > Tool calls
   - Tool results are AUTHORITATIVE but only when needed

EXAMPLES OF CORRECT RESPONSES:

Question: "How do I change the hostname?"
CORRECT: "Use `hostname [name]` in global configuration mode. Example: `hostname Router1`."

Question: "What does no shutdown do?"
CORRECT: "The `no shutdown` command enables an interface and brings it up."

Question: "I'm trying to configure an IP address but getting an error" [with CLI showing: ip address 128.107.20.1/24]
CORRECT: "You're using CIDR notation (/24), but Cisco IOS requires a subnet mask. Use: `ip address 128.107.20.1 255.255.255.0`"

Question: "I'm trying to configure my router's ip address but I'm getting an error" [with CLI showing Floor14(config)# and "ip add 128.107.20.1 255.255.255.0" producing error]
CORRECT: "You're in global config mode, but `ip address` must be run in interface config mode. First enter an interface: `interface GigabitEthernet0/0`, then run: `ip address 128.107.20.1 255.255.255.0`"

Question: "How do I configure an IP address?"
CORRECT: "In interface config mode, use `ip address [address] [mask]`. Example: `ip address 192.168.1.1 255.255.255.0`."

CRITICAL OUTPUT RULES:
- NEVER include XML/HTML tags like <TOOLCALL>, <THINKING>, etc. in your response
- Output ONLY plain text with markdown formatting (bold, code blocks, etc.)
- Your response should be readable text, not internal reasoning or tool metadata

STAY FOCUSED: Answer ONLY what was asked using ONLY the provided documentation. Be brief, accurate, and helpful.
"""

    # CRITICAL: Determine if we should allow tool use
    # If student has CLI errors visible, we should analyze those errors directly
    # NOT call tools to get more config
    has_cli_errors = False
    if cli_history:
        for cmd_entry in cli_history[-5:]:
            output = cmd_entry.get("output", "")
            if "Invalid input" in output or "% " in output or "Incomplete command" in output:
                has_cli_errors = True
                break

    # Disable tools when CLI errors are present
    tools_to_use = [] if has_cli_errors else tools.TOOL_DEFINITIONS
    print(f"[DEBUG] Has CLI errors: {has_cli_errors}, Tools available: {len(tools_to_use)}", flush=True)

    # Prepare messages with reasoning mode
    system_prompt_with_reasoning = f"detailed thinking on\n\n{system_prompt}"
    messages = [
        {"role": "system", "content": system_prompt_with_reasoning}
    ]

    # Add recent conversation history
    for msg in conversation_history[-4:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": student_question})

    # Two-phase approach for streaming with tool support:
    # Phase 1: Check if tools are needed (quick non-streaming call)
    # Phase 2: Stream the response
    # This adds 1-2 seconds latency when tools are used, but ensures grounding in live device state
    import asyncio
    import json
    from orchestrator import tools

    # Use the tools_to_use variable (which may be empty if CLI errors present)
    # Build kwargs dynamically to avoid passing tool_choice when no tools
    create_kwargs = {
        "model": llm_config["model"],
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.6,
        "top_p": 0.95,
        "stream": False,  # Non-streaming to check for tool calls
    }

    # Only add tools and tool_choice if tools are available
    if tools_to_use:
        create_kwargs["tools"] = tools_to_use
        create_kwargs["tool_choice"] = "auto"

    initial_response = llm_client.chat.completions.create(**create_kwargs)

    # Check if the LLM wants to call tools
    choice = initial_response.choices[0]

    print(f"[DEBUG] LLM wants to call tools: {choice.message.tool_calls is not None}", flush=True)
    if choice.message.tool_calls:
        print(f"[DEBUG] Number of tool calls: {len(choice.message.tool_calls)}", flush=True)

    logger.info(f"[FEEDBACK_NODE_STREAM] LLM response - tool_calls: {choice.message.tool_calls is not None}")

    if choice.message.tool_calls:
        logger.info(f"[FEEDBACK_NODE_STREAM] LLM requested {len(choice.message.tool_calls)} tool calls")
        # Execute tool calls
        yield {
            "type": "info",
            "message": "Retrieving device configuration..."
        }
        await asyncio.sleep(0)

        for tool_call in choice.message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            logger.info(f"[FEEDBACK_NODE_STREAM] Calling tool: {function_name}({function_args})")

            # Execute the tool
            if function_name in tools.TOOL_IMPLEMENTATIONS:
                tool_result = await tools.TOOL_IMPLEMENTATIONS[function_name](**function_args)
                logger.info(f"[FEEDBACK_NODE_STREAM] Tool result length: {len(str(tool_result))} chars")
                logger.info(f"[FEEDBACK_NODE_STREAM] Tool result preview: {str(tool_result)[:300]}...")

                # Add assistant's tool call and tool result to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })

        # Now stream the final response with tool results
        response = llm_client.chat.completions.create(
            model=llm_config["model"],
            messages=messages,
            max_tokens=2048,
            temperature=0.6,
            top_p=0.95,
            stream=True
        )
    else:
        # No tools needed, stream the original response
        # We need to re-call with streaming since we got non-streaming above
        response = llm_client.chat.completions.create(
            model=llm_config["model"],
            messages=messages,
            max_tokens=2048,
            temperature=0.6,
            top_p=0.95,
            stream=True
        )

    # Stream chunks to the client
    logger.info("[FEEDBACK_NODE_STREAM] Starting to stream response to client")
    full_response = ""
    chunk_count = 0
    for chunk in response:
        delta = chunk.choices[0].delta

        if delta.content:
            chunk_count += 1
            # Filter out any tool calling artifacts that might slip through
            filtered_content = delta.content
            # Remove <TOOLCALL>...</TOOLCALL> tags and their contents
            import re
            filtered_content = re.sub(r'<TOOLCALL>.*?</TOOLCALL>', '', filtered_content, flags=re.DOTALL)
            # Remove other potential artifacts
            filtered_content = re.sub(r'</?THINKING>', '', filtered_content)

            if filtered_content:  # Only yield if there's content after filtering
                full_response += filtered_content
                yield {
                    "type": "content",
                    "text": filtered_content
                }
                await asyncio.sleep(0)

    logger.info(f"[FEEDBACK_NODE_STREAM] Streamed {chunk_count} chunks, total response length: {len(full_response)} chars")
    logger.info(f"[FEEDBACK_NODE_STREAM] Final response: {full_response}")
    logger.info("=" * 80)

    # The full response has been streamed
    # The tutor's ask_stream method will handle state updates after this completes
