# Stage 1: Build the application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY package.json package-lock.json* ./

# Install dependencies (npm ci is preferred for clean builds if package-lock is present)
RUN npm install

# Copy the rest of the application code
COPY . .

# Ensure the public directory exists so the copy in the next stage doesn't fail
RUN mkdir -p public

# Build the Next.js application
RUN npm run build

# Stage 2: Production environment
FROM node:20-alpine AS runner

WORKDIR /app

# Set environment to production
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# We don't need the entire project, just the built output and dependencies
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Expose the port Next.js runs on
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
