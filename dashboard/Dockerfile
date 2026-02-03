FROM node:20-alpine AS builder
WORKDIR /app


ARG NEXT_PUBLIC_API_URL=https://discordbot-api-latest.onrender.com
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

ENV HOSTNAME="0.0.0.0"
ENV PORT=10000

EXPOSE 10000

CMD ["node", "server.js"]