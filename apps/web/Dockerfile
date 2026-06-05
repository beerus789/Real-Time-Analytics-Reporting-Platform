FROM node:20-bookworm-slim AS runner
WORKDIR /app
COPY package*.json ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm install \
    && npx playwright install --with-deps chromium
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
