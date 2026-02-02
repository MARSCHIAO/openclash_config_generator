#!/usr/bin/env python3
"""
OpenClash Overwrite Generator
根据 YAML 配置生成标准覆写文件
"""

import yaml
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader


class OverwriteGenerator:
    """覆写文件生成器"""
    
    TEMPLATES = {
        'main': {'file': 'main.conf.j2', 'suffix': ''},
        'bypass': {'file': 'bypass.conf.j2', 'suffix': '-bypass'},
        'smart': {'file': 'smart.conf.j2', 'suffix': '-smart'}
    }

    def __init__(self, template_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.logger = logging.getLogger(__name__)

    def analyze_yaml(self, yaml_path: Path) -> Optional[Dict]:
        """分析 YAML 文件"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                return None

            proxy_providers = config.get('proxy-providers', {}) or {}
            
            # 提取 provider 信息
            providers = []
            for name, cfg in proxy_providers.items():
                if isinstance(cfg, dict):
                    providers.append({
                        'name': name,
                        'type': cfg.get('type', 'http'),
                        'url': cfg.get('url', ''),
                        'interval': cfg.get('interval', 86400),
                        'path': cfg.get('path', '')
                    })

            return {
                'proxy_providers': providers,
                'count': len(providers),
                'name': yaml_path.stem
            }
            
        except Exception as e:
            self.logger.error(f"分析失败 {yaml_path}: {e}")
            return None

    def generate_overwrite(self, yaml_path: Path, output_path: Path,
                          template_type: str, repo_url: str,
                          source_type: str = "external") -> bool:
        """生成单个覆写文件"""
        analysis = self.analyze_yaml(yaml_path)
        if not analysis or analysis['count'] == 0:
            self.logger.warning(f"跳过 {yaml_path}: 无有效 provider")
            return False

        # 构建 YAML 下载 URL
        rel_path = yaml_path.name  # 简化处理，实际应根据目录结构调整
        yaml_url = f"{repo_url}/processed_configs/{rel_path}"

        template = self.env.get_template(self.TEMPLATES[template_type]['file'])
        
        content = template.render(
            config_name=analysis['name'],
            source_type=source_type,
            provider_count=analysis['count'],
            proxy_providers=analysis['proxy_providers'],
            yaml_url=yaml_url,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"生成: {output_path}")
        return True

    def process_batch(self, input_dir: Path, output_dir: Path,
                     types: List[str], repo_url: str,
                     source_type: str = "external") -> Dict:
        """批量处理"""
        stats = {'success': 0, 'failed': 0, 'files': []}
        
        for yaml_file in input_dir.rglob('*.yaml'):
            rel_parts = yaml_file.relative_to(input_dir).parts
            base_name = '-'.join(rel_parts[:-1] + (yaml_file.stem,))
            
            for t in types:
                suffix = self.TEMPLATES[t]['suffix']
                out_name = f"Overwrite-{source_type}-{base_name}{suffix}.conf"
                out_path = output_dir / out_name
                
                if self.generate_overwrite(yaml_file, out_path, t, repo_url, source_type):
                    stats['success'] += 1
                    stats['files'].append(str(out_path))
                else:
                    stats['failed'] += 1
        
        return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=Path, required=True)
    parser.add_argument('--output', '-o', type=Path, required=True)
    parser.add_argument('--templates', '-t', type=Path, default=Path('templates'))
    parser.add_argument('--types', nargs='+', default=['main', 'bypass', 'smart'])
    parser.add_argument('--repo-url', default='https://raw.githubusercontent.com/USER/REPO/main')
    parser.add_argument('--source', default='mixed', help='配置来源标识')
    parser.add_argument('-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.v else logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    gen = OverwriteGenerator(args.templates)
    stats = gen.process_batch(args.input, args.output, args.types, args.repo_url, args.source)
    
    print(f"\n✅ 成功: {stats['success']}, ❌ 失败: {stats['failed']}")


if __name__ == '__main__':
    main()
