# Build stage
FROM node:18-alpine as build-stage

WORKDIR /app

COPY package*.json ./

# 安装依赖
RUN npm install --registry https://registry.npmmirror.com

COPY . .

# 构建
RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage

# 复制构建结果到 Nginx 目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
