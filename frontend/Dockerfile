#FROM node:16-alpine
FROM revotech2017/mivaa-agentnexus-frontend:base

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Set a build-time argument for the API URL
# ARG REACT_APP_API_BASE_URL
# ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL
RUN env
# Build the application
RUN npm run build

# Install serve to run the application
RUN npm install -g serve

# Expose the port the app runs on
EXPOSE 3000

# Command to run the application
CMD ["serve", "-s", "build", "-l", "3000"] 
