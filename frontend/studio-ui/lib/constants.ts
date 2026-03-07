// ============================================================================
// Application Constants
// ============================================================================

/**
 * Service URLs — resolved from env vars with localhost fallbacks for dev.
 */
export const AGENT_GENERATOR_URL =
  process.env.NEXT_PUBLIC_AGENT_GENERATOR_URL || 'http://localhost:4521';

export const DOCKER_ORCHESTRATOR_URL =
  process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:4522';

export const CONTROL_ROOM_URL =
  process.env.NEXT_PUBLIC_CONTROL_ROOM_URL || 'http://localhost:4528';
