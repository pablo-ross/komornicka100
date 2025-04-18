FROM node:18-alpine

WORKDIR /app

# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED 1

# Copy package.json first
COPY package.json ./

# If package-lock.json exists, copy it and use npm ci for faster installs
# If not, use regular npm install
COPY package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy the rest of the application
COPY . .

# Start development server
CMD ["npm", "run", "dev"]