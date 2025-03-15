# Build stage
FROM node:18-alpine as build-stage

# Set working directory
WORKDIR /app

# Change to the minute_empire_frontend directory
WORKDIR /app/minute_empire_frontend

# Copy package.json and package-lock.json
COPY minute_empire_frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy project files
COPY minute_empire_frontend/ .

# Build app
RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage

# Copy built files from build stage
COPY --from=build-stage /app/minute_empire_frontend/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 