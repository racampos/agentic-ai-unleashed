# Data Directory Structure

This directory contains all lab-related content organized by purpose.

## Directory Overview

```
data/
├── labs/           # Student-facing lab instructions
├── lessons/        # AI tutor context (invisible to students)
├── topologies/     # YAML topology definitions
└── diagrams/       # Network topology diagrams (PNG)
```

## Labs Directory

Contains markdown files with lab instructions that students see in the UI.

**File Format:**
- YAML frontmatter with metadata
- Markdown content with objectives, scenario, requirements
- Addressing tables
- Step-by-step instructions

**Frontmatter Fields:**
- `id`: Unique lab identifier (e.g., "01-basic-device-configuration")
- `title`: Display title
- `description`: Brief summary for lab cards
- `difficulty`: beginner | intermediate | advanced
- `estimated_time`: Minutes to complete
- `topology_file`: Reference to YAML topology (in topologies/)
- `diagram_file`: Reference to PNG diagram (in diagrams/)
- `lesson_file`: Reference to concept file (in lessons/) for AI RAG
- `prerequisites`: Array of prerequisite lab IDs

**Current Labs:**
- `01-basic-device-configuration.md` - Full configuration with IPv4/IPv6
- `01-basic-routing.md` - Basic router setup
- `02-static-routing.md` - Static route configuration

## Lessons Directory

Contains tutorial/concept content used exclusively by the AI tutor for RAG retrieval.

**Purpose:**
- Provide background theory and concepts
- Help AI tutor explain networking fundamentals
- Never displayed directly to students

**Current Lessons:**
- `01_basic_device_configuration.md` - Device configuration concepts

## Topologies Directory

Contains YAML topology definitions for deploying lab environments to the simulator.

**File Format:**
```yaml
devices:
  - type: router | switch | host
    name: Device-Name
    hardware: cisco_2911 | cisco_2960 | host
    device_id: UUID
    config: |
      Initial configuration
    debug: true

connections:
  - interfaces:
      - device: Device-Name
        interface: InterfaceName
      - device: Device-Name
        interface: InterfaceName
```

**Current Topologies:**
- `01-basic-device-configuration.yaml` - 7-device topology with router, switches, and hosts

## Diagrams Directory

Contains PNG network topology diagrams.

**File Naming:** Match the lab ID with underscores (e.g., `01_basic_device_configuration.png`)

**Current Diagrams:**
- `01_basic_device_configuration.png`

## File Relationships

Each complete lab consists of:

1. **Lab Instructions** (`labs/*.md`)
   - Student-facing content
   - References topology, diagram, and lesson files

2. **Topology Definition** (`topologies/*.yaml`)
   - Deployed to simulator when "Start Lab" is pressed
   - Defines devices and connections

3. **Network Diagram** (`diagrams/*.png`)
   - Visual representation of topology
   - Displayed in lab sidebar

4. **Lesson Content** (`lessons/*.md`) [Optional]
   - AI tutor context for answering questions
   - Retrieved via RAG when relevant to student queries

## Adding a New Lab

1. Create lab instructions: `data/labs/{id}.md` with frontmatter
2. Create topology: `data/topologies/{id}.yaml`
3. Create diagram: `data/diagrams/{id}.png`
4. (Optional) Create lesson: `data/lessons/{id}.md` for AI context
5. Update RAG embeddings index

## Notes

- Lab IDs use hyphens (e.g., `01-basic-device-configuration`)
- File references in frontmatter should match exactly
- Topology files must be valid YAML and match simulator schema
- Diagrams should clearly show device names and connections
