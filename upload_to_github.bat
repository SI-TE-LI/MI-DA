@echo off
setlocal
cd /d D:\HTML

REM 把下面这行替换成你刚才复制的 GitHub 仓库 HTTPS 地址
set REPO_URL=https://github.com/SI-TE-LI/MI-DA.git

echo [1/6] 初始化 Git 仓库...
git init

echo [2/6] 添加所有文件和子文件夹...
git add .

echo [3/6] 提交更改...
git commit -m "Initial upload from D:\HTML"

echo [4/6] 将主分支重命名为 main...
git branch -M main

echo [5/6] 设置远程仓库...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo [6/6] 推送到 GitHub...
git push -u origin main

echo.
echo 上传完成！按任意键退出。
pause