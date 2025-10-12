# Minimal static server for pure HTML/CSS/JS
FROM nginx:1.27-alpine

# Copy custom nginx configuration for development
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    # Disable caching for development \
    add_header Cache-Control "no-store, no-cache, must-revalidate"; \
}' > /etc/nginx/conf.d/default.conf

# Copy site into the default nginx html directory (will be overridden by volume mount in dev)
COPY . /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
