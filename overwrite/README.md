# OpenClash 覆写配置库

本目录按来源分类存放自动生成的覆写配置文件。

## 📂 目录结构

```
overwrite/
├── General_Config/     # 来自 HenryChiao 通用配置
│   ├── README.md       # 该分类说明
│   └── Overwrite-*.conf  # 9种配置变体
├── Smart_Mode/         # 来自 HenryChiao Smart 配置
│   ├── README.md
│   └── Overwrite-*.conf
└── cleaner_config/     # 来自本地自定义配置
    ├── README.md
    └── Overwrite-*.conf
```

## 🚀 快速使用

1. 进入对应来源目录
2. 查看该目录的 README.md 了解配置详情
3. 选择适合的配置变体（标准/Smart/旁路由/LGBM/IPv6）
4. 在 OpenClash 中应用并设置环境变量

## 📝 配置变体说明

每个原始 YAML 生成 9 种配置：

| 后缀 | 模式 | IPv6 | LGBM | 特殊要求 |
|------|------|------|------|----------|
| 无 | 标准 | ✅ | ❌ | 无 |
| `-noipv6` | 标准 | ❌ | ❌ | 无 |
| `-bypass` | 标准 | ❌ | ❌ | **需 EN_DNS** |
| `-smart` | Smart | ✅ | ❌ | 无 |
| `-smart-noipv6` | Smart | ❌ | ❌ | 无 |
| `-smart-LGBM` | Smart | ✅ | ✅ | 无 |
| `-smart-noipv6-LGBM` | Smart | ❌ | ✅ | 无 |
| `-smart-bypass` | Smart | ❌ | ❌ | **需 EN_DNS** |
| `-smart-bypass-LGBM` | Smart | ❌ | ✅ | **需 EN_DNS** |

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

## 📊 构建信息

- 最后更新: 2026-02-02 14:15:13 UTC
- 仓库: https://github.com/MARSCHIAO/openclash_config_generator
- 分支: main

