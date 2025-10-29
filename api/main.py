"""
FastAPI Server for AI Networking Lab Tutor

This server provides REST API endpoints for the frontend web application
to interact with the LangGraph tutoring agent and NetGSim simulator.
"""

import sys
import os
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from orchestrator.tutor import NetworkingLabTutor
from simulator.netgsim_client import NetGSimClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Networking Lab Tutor API",
    description="Backend API for interactive networking labs with AI guidance",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use proper session management)
tutor_sessions: Dict[str, NetworkingLabTutor] = {}
simulator_client: Optional[NetGSimClient] = None


# ========================================
# Request/Response Models
# ========================================

class StartLabRequest(BaseModel):
    """Request to start a new lab session."""
    lab_id: str
    mastery_level: str = "novice"  # "novice", "intermediate", "advanced"


class ChatRequest(BaseModel):
    """Request for student to ask a question."""
    session_id: str
    message: str
    cli_history: Optional[List[Dict[str, str]]] = []


class AnalyzeCommandRequest(BaseModel):
    """Request to analyze a CLI command execution."""
    session_id: str
    command: str
    output: str
    device_id: str
    cli_history: List[Dict[str, str]]


class CreateDeviceRequest(BaseModel):
    """Request to create a simulator device."""
    session_id: str
    device_id: str
    device_type: str
    config: Optional[Dict] = None


class SetupTopologyRequest(BaseModel):
    """Request to set up network topology for a lab."""
    session_id: str
    lab_id: str


class LabMetadata(BaseModel):
    """Lab metadata from frontmatter."""
    id: str
    title: str
    description: str
    difficulty: str
    estimated_time: int
    topology_file: Optional[str] = None
    diagram_file: Optional[str] = None
    lesson_file: Optional[str] = None
    prerequisites: List[str] = []


class Lab(BaseModel):
    """Complete lab information including content."""
    metadata: LabMetadata
    content: str  # Markdown content without frontmatter


# ========================================
# Lab Data Access
# ========================================

# Get the data directory path
DATA_DIR = Path(__file__).parent.parent / "data"
LABS_DIR = DATA_DIR / "labs"
DIAGRAMS_DIR = DATA_DIR / "diagrams"
TOPOLOGIES_DIR = DATA_DIR / "topologies"


def parse_lab_frontmatter(content: str) -> tuple[Dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Returns: (metadata_dict, content_without_frontmatter)
    """
    if not content.startswith("---"):
        return {}, content

    # Find the closing ---
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_yaml = parts[1].strip()
    markdown_content = parts[2].strip()

    try:
        metadata = yaml.safe_load(frontmatter_yaml)
        return metadata or {}, markdown_content
    except yaml.YAMLError as e:
        logger.error(f"Error parsing frontmatter: {e}")
        return {}, content


def load_lab(lab_id: str) -> Lab:
    """Load a lab by ID from the labs directory."""
    lab_file = LABS_DIR / f"{lab_id}.md"

    if not lab_file.exists():
        raise FileNotFoundError(f"Lab file not found: {lab_id}")

    content = lab_file.read_text()
    metadata_dict, markdown_content = parse_lab_frontmatter(content)

    # Ensure required fields
    if "id" not in metadata_dict:
        metadata_dict["id"] = lab_id

    metadata = LabMetadata(**metadata_dict)

    return Lab(metadata=metadata, content=markdown_content)


def list_labs() -> List[LabMetadata]:
    """List all available labs with their metadata."""
    labs = []

    if not LABS_DIR.exists():
        logger.warning(f"Labs directory not found: {LABS_DIR}")
        return labs

    for lab_file in LABS_DIR.glob("*.md"):
        try:
            content = lab_file.read_text()
            metadata_dict, _ = parse_lab_frontmatter(content)

            # Use filename as ID if not in metadata
            if "id" not in metadata_dict:
                metadata_dict["id"] = lab_file.stem

            metadata = LabMetadata(**metadata_dict)
            labs.append(metadata)
        except Exception as e:
            logger.error(f"Error loading lab {lab_file}: {e}")
            continue

    # Sort by ID
    labs.sort(key=lambda x: x.id)

    return labs


def load_topology(topology_filename: str) -> Dict:
    """Load a topology YAML file."""
    topology_file = TOPOLOGIES_DIR / topology_filename

    if not topology_file.exists():
        raise FileNotFoundError(f"Topology file not found: {topology_filename}")

    content = topology_file.read_text()
    topology = yaml.safe_load(content)

    return topology


async def deploy_topology(topology: Dict) -> Dict[str, List]:
    """
    Deploy a topology to the simulator.

    Args:
        topology: Dictionary with 'devices' and 'connections' keys

    Returns:
        Dict with 'devices_created' list and 'connections_info' list
    """
    if not simulator_client:
        raise ValueError("Simulator client not available")

    devices_created = []
    connections_info = []

    # Create all devices
    devices = topology.get("devices", [])
    for device_spec in devices:
        try:
            device_type = device_spec["type"]
            device_name = device_spec["name"]
            hardware = device_spec.get("hardware", device_type)
            config_str = device_spec.get("config", "")

            logger.info(f"Creating device: {device_name} ({device_type}/{hardware})")

            device = await simulator_client.create_device(
                device_id=device_name,
                device_type=device_type,
                hardware=hardware,
                config={"startup_config": config_str} if config_str else None
            )

            devices_created.append({
                "id": device.device_id,
                "type": device.device_type,
                "status": device.status
            })

        except Exception as e:
            logger.error(f"Error creating device {device_spec.get('name')}: {e}")
            # Continue with other devices
            devices_created.append({
                "id": device_spec.get("name"),
                "type": device_spec.get("type"),
                "status": "error",
                "error": str(e)
            })

    # Note: Connections are currently not supported via API
    # The simulator may auto-connect based on device configuration
    # or require manual WebSocket commands
    connections = topology.get("connections", [])
    for conn in connections:
        connections_info.append({
            "interfaces": conn.get("interfaces", []),
            "status": "pending_configuration"
        })

    return {
        "devices_created": devices_created,
        "connections_info": connections_info
    }


# ========================================
# Startup/Shutdown
# ========================================

@app.on_event("startup")
async def startup_event():
    """Initialize simulator client on startup."""
    global simulator_client
    try:
        simulator_client = NetGSimClient()
        health = await simulator_client.health_check()
        logger.info(f"Connected to NetGSim simulator: {health}")
    except Exception as e:
        logger.error(f"Failed to connect to simulator: {e}")
        logger.warning("Simulator features will be unavailable")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    if simulator_client:
        await simulator_client.close()
        logger.info("Simulator client closed")


# ========================================
# Health Check
# ========================================

@app.get("/health")
async def health_check():
    """Check if API is healthy."""
    simulator_status = "unavailable"
    if simulator_client:
        try:
            await simulator_client.health_check()
            simulator_status = "healthy"
        except:
            simulator_status = "error"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "simulator": simulator_status
    }


# ========================================
# Lab Discovery Endpoints
# ========================================

@app.get("/api/v1/labs")
async def get_labs():
    """
    List all available labs with their metadata.

    Returns a list of lab metadata including:
    - id, title, description
    - difficulty, estimated_time
    - Prerequisites
    """
    try:
        labs = list_labs()
        return {
            "labs": [lab.dict() for lab in labs],
            "count": len(labs)
        }
    except Exception as e:
        logger.error(f"Error listing labs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/labs/{lab_id}")
async def get_lab_details(lab_id: str):
    """
    Get complete lab details including instructions.

    Returns:
    - Full lab metadata
    - Markdown content with objectives, scenario, requirements
    """
    try:
        lab = load_lab(lab_id)
        return lab.dict()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Lab not found: {lab_id}")
    except Exception as e:
        logger.error(f"Error loading lab {lab_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/labs/{lab_id}/diagram")
async def get_lab_diagram(lab_id: str):
    """
    Serve the network topology diagram for a lab.

    Returns the PNG diagram file.
    """
    try:
        # Load lab to get diagram filename from metadata
        lab = load_lab(lab_id)

        if not lab.metadata.diagram_file:
            raise HTTPException(status_code=404, detail=f"No diagram configured for lab: {lab_id}")

        diagram_path = DIAGRAMS_DIR / lab.metadata.diagram_file

        if not diagram_path.exists():
            raise HTTPException(status_code=404, detail=f"Diagram file not found: {lab.metadata.diagram_file}")

        return FileResponse(diagram_path, media_type="image/png")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving diagram for lab {lab_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/labs/{lab_id}/start")
async def start_lab_topology(lab_id: str):
    """
    Deploy the topology for a lab to the simulator.

    This creates all devices defined in the lab's topology file.

    Returns:
        - devices_created: List of devices that were created
        - connections_info: List of connections (for future use)
    """
    try:
        # Load lab metadata to get topology file
        lab = load_lab(lab_id)

        if not lab.metadata.topology_file:
            raise HTTPException(status_code=404, detail=f"No topology configured for lab: {lab_id}")

        # Load topology
        topology = load_topology(lab.metadata.topology_file)

        # Deploy to simulator
        result = await deploy_topology(topology)

        logger.info(f"Topology deployed for lab {lab_id}: {len(result['devices_created'])} devices")

        return {
            "lab_id": lab_id,
            "devices_created": result["devices_created"],
            "connections_info": result["connections_info"],
            "message": f"Deployed {len(result['devices_created'])} devices for lab {lab.metadata.title}"
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error deploying topology for lab {lab_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Lab Session Management
# ========================================

@app.post("/api/lab/start")
async def start_lab(request: StartLabRequest):
    """
    Start a new lab session.

    Creates a new tutoring session and returns session ID.
    Optionally sets up simulator topology for the lab.
    """
    try:
        # Create new tutor instance
        tutor = NetworkingLabTutor()

        # Start the lab
        result = tutor.start_lab(
            lab_id=request.lab_id,
            mastery_level=request.mastery_level
        )

        # Store session
        session_id = result["session_id"]
        tutor_sessions[session_id] = tutor

        logger.info(f"Started lab session: {session_id} for lab {request.lab_id}")

        return {
            "session_id": session_id,
            "message": result["response"],
            "lab_id": request.lab_id
        }

    except Exception as e:
        logger.error(f"Error starting lab: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lab/progress/{session_id}")
async def get_progress(session_id: str):
    """Get current lab progress for a session."""
    if session_id not in tutor_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    tutor = tutor_sessions[session_id]
    progress = tutor.get_progress()

    return progress


# ========================================
# Chat/Question Endpoints
# ========================================

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Student asks a question to the AI tutor.

    This endpoint handles general questions, requests for help,
    and any student input that isn't a direct CLI command.
    """
    if request.session_id not in tutor_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    tutor = tutor_sessions[request.session_id]

    try:
        # Log CLI history received
        logger.info(f"Chat request - CLI history entries: {len(request.cli_history) if request.cli_history else 0}")
        if request.cli_history:
            logger.info(f"CLI history sample: {request.cli_history[:2]}")  # Log first 2 entries

        # Update state with CLI history if provided
        if request.cli_history and tutor.state:
            tutor.state["cli_history"] = request.cli_history
            logger.info(f"Updated tutor state with {len(request.cli_history)} CLI history entries")

        # Get response from tutor
        response = tutor.ask(request.message)

        logger.info(f"Chat response for session {request.session_id}")

        return {
            "response": response["response"],
            "suggested_command": response.get("command_executed"),
            "next_suggestion": response.get("next_suggestion"),
            "progress": response["progress"],
            "hints_remaining": response["hints_remaining"]
        }

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-command")
async def analyze_command(request: AnalyzeCommandRequest):
    """
    Analyze a CLI command that the student just executed.

    The frontend calls this after every command execution.
    The AI analyzes the command and output, and decides whether
    to provide feedback, remain silent, or offer suggestions.
    """
    if request.session_id not in tutor_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    tutor = tutor_sessions[request.session_id]

    try:
        # Update CLI history in state
        if tutor.state:
            tutor.state["cli_history"] = request.cli_history
            tutor.state["current_device_id"] = request.device_id

        # Construct analysis request
        analysis_message = f"I just ran the command '{request.command}' and got this output: {request.output[:500]}"

        # Get AI response (it will use cli_analysis_node internally)
        response = tutor.ask(analysis_message)

        # Check if AI decided to intervene
        ai_responded = response["response"] and len(response["response"]) > 0

        logger.info(f"Command analysis for session {request.session_id}: intervened={ai_responded}")

        return {
            "should_display_feedback": ai_responded,
            "feedback": response["response"] if ai_responded else None,
            "suggested_command": response.get("command_executed"),
            "warning": None,  # Could be extracted from response
        }

    except Exception as e:
        logger.error(f"Error analyzing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Simulator Device Management
# ========================================

@app.post("/api/simulator/device/create")
async def create_device(request: CreateDeviceRequest):
    """
    Create a new device in the simulator.

    This is typically called by the AI tutor or when setting up
    a lab topology, not directly by the student.
    """
    if not simulator_client:
        raise HTTPException(status_code=503, detail="Simulator unavailable")

    if request.session_id not in tutor_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        device = await simulator_client.create_device(
            device_id=request.device_id,
            device_type=request.device_type,
            config=request.config
        )

        # Update tutor state with new device
        tutor = tutor_sessions[request.session_id]
        if tutor.state:
            if "simulator_devices" not in tutor.state:
                tutor.state["simulator_devices"] = {}
            tutor.state["simulator_devices"][device.device_id] = {
                "type": device.device_type,
                "config": device.config,
                "status": device.status
            }

        logger.info(f"Created device: {device.device_id} for session {request.session_id}")

        return {
            "device_id": device.device_id,
            "device_type": device.device_type,
            "status": device.status
        }

    except Exception as e:
        logger.error(f"Error creating device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/simulator/devices")
async def list_devices():
    """List all devices in the simulator."""
    if not simulator_client:
        raise HTTPException(status_code=503, detail="Simulator unavailable")

    try:
        devices = await simulator_client.list_devices()

        return {
            "devices": [
                {
                    "device_id": d.device_id,
                    "device_type": d.device_type,
                    "status": d.status
                }
                for d in devices
            ]
        }

    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulator/topology/setup")
async def setup_topology(request: SetupTopologyRequest):
    """
    Set up network topology for a specific lab.

    This creates the necessary devices and connections based on
    the lab requirements.
    """
    if not simulator_client:
        raise HTTPException(status_code=503, detail="Simulator unavailable")

    if request.session_id not in tutor_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Define topology for different labs
        # TODO: Load from lab metadata
        topology_map = {
            "01-basic-routing": [
                {"device_id": "router1", "device_type": "router", "config": None},
            ],
            "02-static-routing": [
                {"device_id": "router1", "device_type": "router", "config": None},
                {"device_id": "router2", "device_type": "router", "config": None},
            ],
        }

        topology = topology_map.get(request.lab_id, [])
        created_devices = []

        # Create each device
        for device_spec in topology:
            device = await simulator_client.create_device(
                device_id=device_spec["device_id"],
                device_type=device_spec["device_type"],
                config=device_spec.get("config")
            )
            created_devices.append({
                "device_id": device.device_id,
                "device_type": device.device_type
            })

        # Update tutor state
        tutor = tutor_sessions[request.session_id]
        if tutor.state:
            tutor.state["simulator_devices"] = {
                d["device_id"]: {"type": d["device_type"], "config": None, "status": "ready"}
                for d in created_devices
            }
            if created_devices:
                tutor.state["current_device_id"] = created_devices[0]["device_id"]

        logger.info(f"Set up topology for lab {request.lab_id}: {len(created_devices)} devices")

        return {
            "devices": created_devices,
            "message": f"Created {len(created_devices)} devices for lab {request.lab_id}"
        }

    except Exception as e:
        logger.error(f"Error setting up topology: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Main Entry Point
# ========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
