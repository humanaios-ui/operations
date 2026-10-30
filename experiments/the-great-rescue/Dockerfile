FROM node:22-alpine
WORKDIR /app
COPY package.json engine.mjs server.mjs ./
COPY public ./public
ENV PORT=8765
EXPOSE 8765
CMD ["node", "server.mjs"]
