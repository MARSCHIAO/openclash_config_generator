#!/usr/bin/env python3
"""
OpenClash Overwrite Generator - 9 配置版本
基于 2 个原配置生成 9 种变体
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

    def generate_overwrite(self, yaml_path: Path, output_path: Path,
                          config_def: Dict, repo_url: str, 
                          source_type: str, input_base: Path) -> bool:
        """生成单个覆写文件"""
        analysis = self.analyze_yaml(yaml_path)
        if not analysis or analysis['count'] == 0:
            self.logger.warning(f"No providers in {yaml_path}, skipping")
            return False

        # 构建下载URL
        rel_parts = yaml_path.relative_to(input_base)
        yaml_url = f"{repo_url}/processed_configs/{source_type}/{rel_parts}"

        try:
            template = self.env.get_template('base.conf.j2')
            
            content = template.render(
                config_name=analysis['name'],
                source_type=source_type,
                provider_count=analysis['count'],
                proxy_providers=analysis['proxy_providers'],
                yaml_url=yaml_url,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                # 配置类型参数
                smart_mode=config_def['smart_mode'],
                bypass_mode=config_def['bypass_mode'],
                enable_ipv6=config_def['enable_ipv6'],
                enable_lgbm=config_def['enable_lgbm']
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Generated: {output_path.name} ({config_def['description']})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate {output_path}: {e}")
            return False

    def process_batch(self, input_dir: Path, output_dir: Path,
                     repo_url: str, source_type: str) -> Dict:
        """批量处理 - 为每个 YAML 生成 9 种配置"""
        stats = {'success': 0, 'failed': 0, 'skipped': 0, 'combinations': []}
        
        yaml_files = list(input_dir.rglob('*.yaml'))
        self.logger.info(f"Found {len(yaml_files)} YAML files in {input_dir}")
        
        for yaml_file in yaml_files:
            for config_def in self.config_types:
                try:
                    # 构建输出文件名
                    base_name = yaml_file.stem
                    suffix = config_def['suffix']
                    
                    # 文件名格式: Overwrite-{source}-{basename}{suffix}.conf
                    # 或: Overwrite{suffix}-{source}-{basename}.conf
                    if suffix:
                        # 有后缀: Overwrite-smart-LGBM-external-xxx.conf
                        filename = f"Overwrite{suffix}-{source_type}-{base_name}.conf"
                    else:
                        # 无后缀: Overwrite-external-xxx.conf
                        filename = f"Overwrite-{source_type}-{base_name}.conf"
                    
                    output_path = output_dir / filename
                    
                    result = self.generate_overwrite(
                        yaml_file, output_path, config_def,
                        repo_url, source_type, input_dir
                    )
                    
                    if result:
                        stats['success'] += 1
                        stats['combinations'].append({
                            'file': filename,
                            'yaml': yaml_file.name,
                            'type': config_def['name'],
                            'desc': config_def['description']
                        })
                    else:
                        stats['skipped'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error processing {yaml_file} [{config_def['name']}]: {e}")
                    stats['failed'] += 1
        
        return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=Path, required=True)
    parser.add_argument('--output', '-o', type=Path, required=True)
    parser.add_argument('--templates', '-t', type=Path, default=Path('templates'))
    parser.add_argument('--config-types', '-c', type=Path, 
                       default=Path('src/config_types.json'))
    parser.add_argument('--repo-url', default='https://raw.githubusercontent.com/USER/REPO/main')
    parser.add_argument('--source', default='external')
    parser.add_argument('--verbose', '-v', action='store_true')
    
    args = parser.parse_args()
    
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    try:
        gen = OverwriteGenerator(args.templates, args.config_types)
        stats = gen.process_batch(args.input, args.output, args.repo_url, args.source)
        
        print(f"\n{'='*60}")
        print(f"生成统计: 成功 {stats['success']}, 跳过 {stats['skipped']}, 失败 {stats['failed']}")
        print(f"{'='*60}")
        
        # 按类型分组显示
        from collections import defaultdict
        by_type = defaultdict(list)
        for item in stats['combinations']:
            by_type[item['type']].append(item['file'])
        
        for type_name, files in sorted(by_type.items()):
            print(f"\n【{type_name}】")
            for f in files[:3]:  # 只显示前3个
                print(f"  - {f}")
            if len(files) > 3:
                print(f"  ... 还有 {len(files)-3} 个")
        
        return 0
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
