FROM node:22-slim

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
# Dev server: proxies /api to the backend service
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
