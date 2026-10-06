# Image 本地候选：构建与使用边界

本地候选将 image 执行器、共享 content-store、源码 Skill、固定字体及许可放在同一目录树。它不更改现有轻量 Skill npm 包边界，不是发布版本，不修改全局安装。模型 Provider 相关文件随源码携带，但不包含用户配置、凭据、node_modules、用户素材或历史验收 dist。

## 构建

在仓库根目录执行，输出父目录须已存在，文件必须是新路径：

```sh
python3 scripts/build_image_candidate.py --output /absolute/new-image-candidate.zip
```

构建器校验字体摘要，并拒绝符号链接和意外文件类型。`candidate.json` 记录每份载荷的 SHA-256 与源码 HEAD；它是包含未提交工作区改动的精确文件快照，不能仅用 Git HEAD 重现。保留前一候选可回退，不覆盖已有包。

## 准备执行环境

先核对压缩包摘要与内部 candidate.json，再在新目录解压。Node >=22；通过包内锁文件安装依赖：

```sh
cd /absolute/extracted/creative-craft-image/integrations/image-production
npm ci --ignore-scripts --no-audit --no-fund
```

字体已捆绑，无需额外下载。`PHOTO-WORKFLOW.md` 给出裁切、模板、修改与导出输入。调用这里的 `cli.mjs` 即可运行；让 Agent 使用时提供解压后的源码 Skill 路径及执行器路径。加载 Skill 不等于全局安装或执行器自动发现。Provider 功能另需 Python >=3.11 与用户授权配置，本次本地验收没有调用它们。

## 已验证与未覆盖

2026-10-05 候选实测：仓库外新目录、没有既有 node_modules、独立 npm 缓存，npm ci 安装 31 个包；裁切、两种模板、改字、重新打开、导出及历史导出全部通过。候选包内图片测试 99/99 通过，执行前后全部载荷文件摘要不变。临时解压目录清理，不动全局安装。

这是同一 macOS 主机 Node v24.18.0 上的隔离目录验证，不是新机器、容器或 Windows/Linux 认证；当前环境变量仍继承主机。没有全局安装、宿主自然语言选路验收、模型调用或发布。候选中的旧 dist 文档链接不随包提供，也不是运行前提。

本地包和完整证据：image-local-candidate-2026-10-05（本机证据，未入库：`../dist/image-local-candidate-2026-10-05/README.md`）。
