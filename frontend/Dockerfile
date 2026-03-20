FROM node:22-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ARG BACKEND_URL=http://127.0.0.1:8000
ENV BACKEND_URL=$BACKEND_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
