# ── Stage 1: Build ────────────────────────────────
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files first (layer caching)
COPY package.json package-lock.json* ./

RUN npm ci --silent

# Copy source code
COPY . .

# Build the app
RUN npm run build

# ── Stage 2: Production ───────────────────────────
FROM nginx:alpine AS runtime

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Non-root user for security
RUN addgroup -g 1001 -S pavlov && \
    adduser -S pavlov -u 1001 && \
    chown -R pavlov:pavlov /var/cache/nginx && \
    chown -R pavlov:pavlov /var/log/nginx && \
    chown -R pavlov:pavlov /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R pavlov:pavlov /var/run/nginx.pid

USER pavlov

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
    --start-period=20s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]