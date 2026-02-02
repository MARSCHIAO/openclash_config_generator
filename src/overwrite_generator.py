#!/usr/bin/env python3
"""
OpenClash Overwrite Generator - 支持多级目录结构
保持完整的分类层级（如 General_Config/Author1/）
"""
import yaml
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader


class OverwriteGenerator:
    def __init__(self, template_dir: Path, config_types_path: Path):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.logger = logging.getLogger(__name__)
        
        with open(config_types_path, 'r') as f:
            self.config_types = json.load(f)['config_types']

    def analyze_yaml(self, yaml_path: Path) -> Optional[Dict]:
        """分析 YAML 文件"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                return None
            
            proxy_providers = config.get('proxy-providers', {}) or {}
            providers = []
            
            for name, cfg in proxy_providers.items():
                if isinstance(cfg, dict):
                    providers.append({
                        'name': name,
                        'type': cfg.get('type', 'http'),
                        'url': cfg.get('url', ''),
                        'interval': cfg.get('interval', 86400)
                    })
            
            return {
                'proxy_providers': providers,
                'count': len(providers),
                'name': yaml_path.stem
            }
        
        except Exception as e:
            self.logger.error(f"Error analyzing {yaml_path}: {e}")
            return None

    def generate_readme(self, category_dir: Path, relative_path: str, 
                       source_type: str, files_generated: List[str]):
        """为每个分类目录生成 README"""
        
        # 解析相对路径，确定说明
        parts = relative_path.split('/')
        if source_type == 'external':
            if len(parts) >= 2:
                main_category = parts[0]  # General_Config 或 Smart_Mode
                sub_category = parts[1]   # 作者名
                
                if main_category == 'General_Config':
                    purpose = f"通用配置 - {sub_category} 作者维护"
                    source_desc = f"HenryChiao/mihomo_yamls/THEYAMLS/{relative_path}"
                elif main_category == 'Smart_Mode':
                    purpose = f"Smart 智能模式 - {sub_category} 作者维护"
                    source_desc = f"HenryChiao/mihomo_yamls/THEYAMLS/{relative_path}"
                else:
                    purpose = "外部同步配置"
                    source_desc = f"HenryChiao/mihomo_yamls/THEYAMLS/{relative_path}"
            else:
                purpose = "外部同步配置"
                source_desc = f"HenryChiao/mihomo_yamls/THEYAMLS/{relative_path}"
        else:
            source_desc = f"本地目录 {relative_path}"
            purpose = "用户自定义配置"
        
        readme_content = f"""# {relative_path} 覆写配置

## 📍 来源
- **路径**: `{source_desc}`
- **类型**: {'外部自动同步' if source_type == 'external' else '本地手动维护'}
- **用途**: {purpose}

## 📁 文件说明

本目录包含以下 9 种配置变体：

| 文件名 | 模式 | IPv6 | LGBM | 适用场景 |
|--------|------|------|------|----------|
| `Overwrite-*.conf` | 标准 | ✅ | ❌ | 主路由，启用 IPv6 |
| `Overwrite-noipv6-*.conf` | 标准 | ❌ | ❌ | 主路由，禁用 IPv6 |
| `Overwrite-bypass-*.conf` | 标准 | ❌ | ❌ | **旁路由**，需 EN_DNS |
| `Overwrite-smart-*.conf` | Smart | ✅ | ❌ | Smart 模式，启用 IPv6 |
| `Overwrite-smart-noipv6-*.conf` | Smart | ❌ | ❌ | Smart 模式，禁用 IPv6 |
| `Overwrite-smart-LGBM-*.conf` | Smart | ✅ | ✅ | Smart + LGBM 模型 |
| `Overwrite-smart-noipv6-LGBM-*.conf` | Smart | ❌ | ✅ | Smart + LGBM，无 IPv6 |
| `Overwrite-smart-bypass-*.conf` | Smart | ❌ | ❌ | **Smart 旁路由**，需 EN_DNS |
| `Overwrite-smart-bypass-LGBM-*.conf` | Smart | ❌ | ✅ | **Smart 旁路由 + LGBM**，需 EN_DNS |

## 🔧 环境变量

### 基础变量（所有配置）
```bash
EN_KEY=你的订阅链接

# 或（多 provider 时）
EN_KEY1=订阅1;EN_KEY2=订阅2;...
```

### 旁路由额外变量（bypass 系列）
```bash
EN_DNS=223.5.5.5,114.114.114.114
```

## 📝 生成信息
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 配置文件数: {len(files_generated)}

---
*由 GitHub Actions 自动生成*
"""
        
        readme_path = category_dir / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.logger.info(f"Generated README: {readme_path}")

    def generate_overwrite(self, yaml_path: Path, output_path: Path, 
                          config_def: Dict, repo_url: str, 
                          relative_path: str, source_type: str) -> bool:
        """生成单个覆写文件"""
        
        analysis = self.analyze_yaml(yaml_path)
        if not analysis or analysis['count'] == 0:
            self.logger.warning(f"No providers in {yaml_path}, skipping")
            return False
        
        # 构建下载URL（保持完整的相对路径）
        yaml_url = f"{repo_url}/processed_configs/{source_type}/{relative_path}/{yaml_path.name}".replace('\\', '/')
        
        try:
            template = self.env.get_template('base.conf.j2')
            content = template.render(
                config_name=analysis['name'],
                source_type=source_type,
                category=relative_path,
                provider_count=analysis['count'],
                proxy_providers=analysis['proxy_providers'],
                yaml_url=yaml_url,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                smart_mode=config_def['smart_mode'],
                bypass_mode=config_def['bypass_mode'],
                enable_ipv6=config_def['enable_ipv6'],
                enable_lgbm=config_def['enable_lgbm']
            )
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to generate {output_path}: {e}")
            return False

    def process_directory_recursive(self, current_dir: Path, input_base: Path, 
                                   output_base: Path, repo_url: str, 
                                   source_type: str, stats: Dict):
        """递归处理目录，保持完整的目录层级"""
        
        yaml_files = list(current_dir.glob('*.yaml'))
        has_yaml = len(yaml_files) > 0
        
        if has_yaml:
            # 计算相对路径（相对于输入基础目录）
            relative_path = str(current_dir.relative_to(input_base))
            output_dir = output_base / relative_path
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"处理分类: {relative_path}")
            self.logger.info(f"输出目录: {output_dir}")
            self.logger.info(f"YAML 文件: {len(yaml_files)} 个")
            
            files_generated = []
            
            # 处理当前目录的所有 YAML 文件
            for yaml_file in yaml_files:
                for config_def in self.config_types:
                    try:
                        # 构建文件名
                        base_name = yaml_file.stem
                        suffix = config_def['suffix']
                        
                        if suffix:
                            filename = f"Overwrite{suffix}-{base_name}.conf"
                        else:
                            filename = f"Overwrite-{base_name}.conf"
                        
                        output_path = output_dir / filename
                        
                        result = self.generate_overwrite(
                            yaml_file, output_path, config_def,
                            repo_url, relative_path, source_type
                        )
                        
                        if result:
                            files_generated.append(filename)
                            stats['total'] += 1
                        else:
                            stats['errors'] += 1
                    
                    except Exception as e:
                        self.logger.error(f"Error: {e}")
                        stats['errors'] += 1
            
            # 生成当前目录的 README
            self.generate_readme(output_dir, relative_path, 
                               source_type, files_generated)
            
            # 记录统计
            if relative_path not in stats['categories']:
                stats['categories'][relative_path] = 0
            stats['categories'][relative_path] += len(files_generated)
        
        # 递归处理子目录
        for sub_dir in current_dir.iterdir():
            if sub_dir.is_dir():
                self.process_directory_recursive(
                    sub_dir, input_base, output_base, 
                    repo_url, source_type, stats
                )

    def process_directory(self, input_dir: Path, output_base: Path, 
                         repo_url: str, source_type: str) -> Dict:
        """处理入口函数"""
        stats = {'categories': {}, 'total': 0, 'errors': 0}
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"开始处理: {input_dir}")
        self.logger.info(f"输出基础: {output_base}")
        self.logger.info(f"来源类型: {source_type}")
        
        # 从输入目录开始递归处理
        self.process_directory_recursive(
            input_dir, input_dir, output_base, 
            repo_url, source_type, stats
        )
        
        return stats


def main():
    parser = argparse.ArgumentParser(
        description='Generate OpenClash overwrite configs from YAML files (supports nested directories)'
    )
    parser.add_argument('--input', '-i', type=Path, required=True,
                       help='输入目录（支持多级子目录）')
    parser.add_argument('--output', '-o', type=Path, required=True,
                       help='输出基础目录')
    parser.add_argument('--templates', '-t', type=Path, 
                       default=Path('templates'))
    parser.add_argument('--config-types', '-c', type=Path,
                       default=Path('src/config_types.json'))
    parser.add_argument('--repo-url', 
                       default='https://raw.githubusercontent.com/USER/REPO/main',
                       help='Repository base URL for YAML downloads')
    parser.add_argument('--source', default='external',
                       help='来源类型: external 或 local')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be generated without writing files')
    
    args = parser.parse_args()
    
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )
    
    try:
        gen = OverwriteGenerator(args.templates, args.config_types)
        
        if args.dry_run:
            logging.info("DRY RUN MODE - No files will be written")
        
        stats = gen.process_directory(
            args.input, args.output, args.repo_url, args.source
        )
        
        print(f"\n{'='*60}")
        print(f"总计生成: {stats['total']} 个文件")
        if stats['errors'] > 0:
            print(f"⚠️  错误数: {stats['errors']}")
        print(f"\n分类统计:")
        for cat, count in sorted(stats['categories'].items()):
            print(f"  - {cat}: {count} 个文件")
        
        return 0
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
