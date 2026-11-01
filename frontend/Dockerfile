# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# BACKEND_URL: internal Docker network address used by Next.js server-side proxy.
# NEXT_PUBLIC_API_URL: left empty so browser calls use relative /api/... paths.
ARG BACKEND_URL=http://backend:4000
ARG NEXT_PUBLIC_API_URL=
ENV BACKEND_URL=${BACKEND_URL}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the Next.js app
RUN npm run build

# Runtime stage
FROM node:20-alpine

WORKDIR /app

# Install dumb-init to handle signals properly
RUN apk add --no-cache dumb-init

# Copy package files
COPY package.json package-lock.json ./

# Install only production dependencies
RUN npm ci --only=production

# Copy built app and public files from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.ts ./

# Expose port
EXPOSE 3000

# Set environment variables for production
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Run Next.js in production mode
CMD ["npm", "start"]
