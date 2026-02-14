# LAIAS Templates

## godzilla_reference.py

The "Gold Standard" reference template for LAIAS agent code generation.

### Purpose
This file serves as the architectural pattern that ALL generated agents must follow.

### Key Patterns
- Flow-based architecture using CrewAI `Flow[AgentState]`
- Typed state management with Pydantic BaseModel
- Event-driven transitions using decorators (`@start`, `@listen`, `@router`)
- Agent factory pattern for specialized agent creation
- Comprehensive error handling with recovery paths
- Built-in analytics and monitoring

### Usage
The Agent Generator API uses this template as the basis for code generation.
Do not hardcode this class into applications. Instead, teach the system:
*"When the user asks for an agent, write code that looks like THIS."*
