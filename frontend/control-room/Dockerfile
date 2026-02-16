# LAIAS Control Room - Dockerfile
# Multi-stage build for production
# Build context: ./frontend (so shared/ is available)

# ============================================================================
# Stage 1: Dependencies
# ============================================================================
FROM node:20-alpine AS deps

WORKDIR /app

# Install dependencies (including devDependencies needed for build)
COPY control-room/package.json control-room/package-lock.json* ./
RUN npm ci

# ============================================================================
# Stage 2: Builder
# ============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./control-room/node_modules

# Copy source files
COPY control-room ./control-room
COPY shared ./shared

WORKDIR /app/control-room

# Set environment variables for build
ARG NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL
ENV NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL=$NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the application
RUN npm run build

# ============================================================================
# Stage 3: Runner
# ============================================================================
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/control-room/.next/standalone ./
COPY --from=builder /app/control-room/.next/static ./.next/static

# Set correct ownership
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3001

ENV PORT=3001
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3001/ || exit 1

# Start the application
CMD ["node", "server.js"]
