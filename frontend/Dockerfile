# Stage 1 — build the React app
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps

COPY . .

# REACT_APP_* variables are baked into the JS bundle at build time.
# Pass them as Railway build arguments in the service settings.
ARG REACT_APP_API_URL=http://localhost:8000
ARG REACT_APP_WS_URL=ws://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL

RUN npm run build

# Stage 2 — serve with nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

# nginx.conf uses ${PORT} which Railway injects at runtime.
# Copy as a template; envsubst replaces ${PORT} before nginx starts.
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Railway sets $PORT dynamically. envsubst substitutes it into the nginx
# config at container startup so nginx listens on the correct port.
CMD ["sh", "-c", "envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
