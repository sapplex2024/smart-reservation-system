# 使用Node.js镜像作为基础镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装所有依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 安装静态文件服务
RUN npm install -g serve

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -O - http://localhost:3000 || exit 1

# 启动命令
CMD ["serve", "-s", "dist", "-l", "3000"]