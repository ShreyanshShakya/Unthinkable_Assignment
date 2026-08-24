FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=development

COPY package*.json ./

RUN npm ci --legacy-peer-deps

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]