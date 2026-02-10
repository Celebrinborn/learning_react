# Build stage
FROM node:slim AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code and env files
COPY . .

# Accept APP_ENV build arg (dev, test, prod) - used by vite.config.ts
ARG APP_ENV=prod
ENV APP_ENV=${APP_ENV}

# Build the application
RUN npm run build

# Runtime stage - serve with nginx
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration as template for envsubst processing.
# Nginx doesn't natively support environment variables in config files. The official nginx:alpine
# image includes an entrypoint script (20-envsubst-on-templates.sh) that runs `envsubst` on all
# *.template files in /etc/nginx/templates/, replacing ${VAR} with env var values, then outputs
# the result to /etc/nginx/conf.d/. This allows one image to work across environments (local,
# Azure, k8s) by setting BACKEND_URL differently in each deployment.
# Search: "nginx docker envsubst", "nginx environment variables docker", "NGINX_ENVSUBST_TEMPLATE_DIR"
COPY default.conf.template /etc/nginx/templates/default.conf.template

# Default backend URL (overridden by Container Apps environment variable)
ENV BACKEND_URL=http://backend:8000

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
