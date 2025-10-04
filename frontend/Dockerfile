FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package.json
COPY package.json ./

<<<<<<< HEAD
# Install dependencies (use npm install instead of npm ci)
=======
# Install dependencies
>>>>>>> f8582f4cdadbe28d6b5b906f010cfcce49c09a83
RUN npm install --production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Install serve to run the app
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Command to run the application
CMD ["serve", "-s", "build", "-l", "3000"]
