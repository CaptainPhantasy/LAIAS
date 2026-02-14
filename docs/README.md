# LAIAS Documentation

## Documents

| Document | Description |
|----------|-------------|
| [OVERVIEW.md](OVERVIEW.md) | Original project description and goals |
| [MASTER_PLAN.md](MASTER_PLAN.md) | Project roadmap and implementation phases |
| [BUILD_GUIDE.md](BUILD_GUIDE.md) | Detailed build and implementation guide |
| [SYSTEM_DIRECTIVES.md](SYSTEM_DIRECTIVES.md) | System-level configuration and protocols |

## Quick Links

- [Root README](../README.md) - Project overview and quick start
- [Implementation Status](../IMPLEMENTATION_STATUS.md) - Current progress tracker

## For Contributors

1. Start with [OVERVIEW.md](OVERVIEW.md) to understand the project goals
2. Read [MASTER_PLAN.md](MASTER_PLAN.md) for the implementation roadmap
3. Follow [BUILD_GUIDE.md](BUILD_GUIDE.md) for detailed setup instructions

## Repository Structure Notes

### Intentional File Nesting

| Pattern | Location | Purpose |
|---------|----------|---------|
| `docker-compose.yml` | Root + `services/docker-orchestrator/` | Root = full stack orchestration; Nested = standalone service development |
| `.env.example` | Root + each service | Root = shared config; Service-specific = adds `SERVICE_PORT` override |
| `Dockerfile` | Each service only | Microservice pattern - each service builds independently |

### Known Technical Debt

- **`.env.example` duplication**: Service-specific `.env.example` files duplicate most content from root. Future improvement: consolidate to root file with service-specific overrides only.
