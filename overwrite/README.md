# OpenClash 覆写配置库

本目录按来源和作者分类存放自动生成的覆写配置文件。

## 📂 目录结构

```
overwrite/
├── General_Config/          # 通用配置
│   ├── Author1/             # 作者1的配置
│   │   ├── README.md
│   │   └── Overwrite-*.conf (9 variants)
│   ├── Author2/             # 作者2的配置
│   │   ├── README.md
│   │   └── Overwrite-*.conf (9 variants)
│   └── ...
├── Smart_Mode/              # Smart 智能模式
│   ├── Author1/
│   │   ├── README.md
│   │   └── Overwrite-*.conf (9 variants)
│   ├── Author2/
│   │   ├── README.md
│   │   └── Overwrite-*.conf (9 variants)
│   └── ...
└── cleaner_config/          # 本地自定义配置
    ├── README.md
    └── Overwrite-*.conf (9 variants)
```

## 🚀 快速使用

1. **选择配置类型**
   - `General_Config/` - 通用配置，适合日常使用
   - `Smart_Mode/` - 智能模式，自动选择最优节点
   - `cleaner_config/` - 本地自定义配置

2. **选择作者/维护者**
   - 进入对应的作者子目录
   - 查看该目录的 README.md 了解配置详情

3. **选择配置变体**
   - 根据你的网络环境选择合适的变体（标准/Smart/旁路由/LGBM/IPv6）

4. **应用配置**
   - 在 OpenClash 中添加覆写配置
   - 设置必要的环境变量

## 📝 配置变体说明

每个原始 YAML 生成 9 种配置变体：

| 后缀 | 模式 | IPv6 | LGBM | 特殊要求 | 典型使用场景 |
|------|------|------|------|----------|-------------|
| 无 | 标准 | ✅ | ❌ | 无 | 主路由，支持 IPv6 |
| `-noipv6` | 标准 | ❌ | ❌ | 无 | 主路由，纯 IPv4 网络 |
| `-bypass` | 标准 | ❌ | ❌ | **需 EN_DNS** | **旁路由模式** |
| `-smart` | Smart | ✅ | ❌ | 无 | 智能选节点，支持 IPv6 |
| `-smart-noipv6` | Smart | ❌ | ❌ | 无 | 智能选节点，纯 IPv4 |
| `-smart-LGBM` | Smart | ✅ | ✅ | 无 | 智能 + AI 优化 |
| `-smart-noipv6-LGBM` | Smart | ❌ | ✅ | 无 | 智能 + AI，纯 IPv4 |
| `-smart-bypass` | Smart | ❌ | ❌ | **需 EN_DNS** | **智能旁路由** |
| `-smart-bypass-LGBM` | Smart | ❌ | ✅ | **需 EN_DNS** | **智能旁路由 + AI** |

## 🔧 环境变量设置

### 基础变量（所有配置必需）

```bash
# 单个订阅
EN_KEY=https://your-subscription-url

# 多个订阅（使用分号分隔）
EN_KEY1=https://subscription1;EN_KEY2=https://subscription2
```

### 旁路由专用变量

使用 `-bypass` 系列配置时必须设置：

```bash
EN_DNS=223.5.5.5,114.114.114.114
```

### 在 OpenClash 中设置环境变量

1. 打开 OpenClash 插件配置页面
2. 找到「覆写设置」→「环境变量」
3. 添加上述对应的变量
4. 保存并应用配置

## ⏰ 自动更新

- **外部配置**: 每日 06:00 UTC 自动同步 HenryChiao 仓库
- **本地配置**: 推送到 `cleaner_config/` 时自动重新生成
- **结构保持**: 完整保留原始仓库的目录结构和分类

## 📊 构建信息

- 最后更新: 2026-02-08 06:44:39 UTC
- 仓库: https://github.com/ChiaoYenta/THE_OPENCLASH_OVERWRITE_AUTO_CONSTRUCTION
- 分支: main

