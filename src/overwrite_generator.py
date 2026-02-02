#!/usr/bin/env python3
"""
Overwrite Generator - 生成 OpenClash 覆写文件
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
    TEMPLATES = {
        'main': {'file': 'main.conf.j2', 'suffix': ''},
        'bypass': {'file': 'bypass.conf.j2', 'suffix': '-bypass'},
        'smart': {'file': 'smart.conf.j2', 'suffix': '-smart'}
    }

    def __init__(self, template_dir: Path):
        if not template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {template_dir}")
            
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

    def generate_filename(self, yaml_path: Path, template_type: str, 
                         source_type: str, input_base: Path) -> str:
        """生成文件名"""
        try:
            rel_path = yaml_path.relative_to(input_base)
            parts = list(rel_path.parent.parts) + [rel_path.stem]
        except ValueError:
            parts = [yaml_path.stem]
        
        # 清理名称
        base_name = '-'.join(parts)
        base_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base_name)
        
        suffix = self.TEMPLATES[template_type]['suffix']
        return f"Overwrite-{source_type}-{base_name}{suffix}.conf"

    def generate(self, yaml_path: Path, output_path: Path, template_type: str,
                 repo_url: str, source_type: str, input_base: Path) -> bool:
        """生成覆写文件"""
        analysis = self.analyze_yaml(yaml_path)
        if not analysis:
            return False
        
        if analysis['count'] == 0:
            self.logger.warning(f"No providers in {yaml_path}, skipping")
            return False

        # 构建下载URL
        rel_parts = yaml_path.relative_to(input_base)
        yaml_url = f"{repo_url}/processed_configs/{source_type}/{rel_parts}"

        try:
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
            
            self.logger.info(f"Generated: {output_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate {output_path}: {e}")
            return False

    def process_batch(self, input_dir: Path, output_dir: Path,
                     types: List[str], repo_url: str,
                     source_type: str) -> Dict:
        """批量处理"""
        stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        yaml_files = list(input_dir.rglob('*.yaml'))
        self.logger.info(f"Found {len(yaml_files)} YAML files in {input_dir}")
        
        for yaml_file in yaml_files:
            for t in types:
                try:
                    filename = self.generate_filename(yaml_file, t, source_type, input_dir)
                    output_path = output_dir / filename
                    
                    if self.generate(yaml_file, output_path, t, repo_url, source_type, input_dir):
                        stats['success'] += 1
                    else:
                        stats['skipped'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error processing {yaml_file}: {e}")
                    stats['failed'] += 1
        
        return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=Path, required=True)
    parser.add_argument('--output', '-o', type=Path, required=True)
    parser.add_argument('--templates', '-t', type=Path, default=Path('templates'))
    parser.add_argument('--types', nargs='+', default=['main', 'bypass', 'smart'])
    parser.add_argument('--repo-url', default='https://raw.githubusercontent.com/USER/REPO/main')
    parser.add_argument('--source', default='external')
    parser.add_argument('--verbose', '-v', action='store_true')
    
    args = parser.parse_args()
    
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    try:
        gen = OverwriteGenerator(args.templates)
        stats = gen.process_batch(
            args.input, args.output, 
            args.types, args.repo_url, args.source
        )
        
        print(f"\n✅ Success: {stats['success']}, ⚠️ Skipped: {stats['skipped']}, ❌ Failed: {stats['failed']}")
        return 0
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
