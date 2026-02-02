#!/usr/bin/env python3
"""
Conf Generator - 基于精简的 YAML 配置生成 OpenClash .conf 覆写文件
根据 proxy-providers 数量动态生成环境变量
"""

import yaml
import logging
import sys
from pathlib import Path
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader


class ConfGenerator:
    """OpenClash .conf 文件生成器"""

    def __init__(self, template_dir: Path):
        """
        初始化生成器
        """
        self.logger = logging.getLogger(__name__)
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def analyze_providers(self, yaml_config: Dict) -> Dict:
        """
        分析配置文件中的 providers
        """
        proxy_providers = yaml_config.get('proxy-providers', {})
        rule_providers = yaml_config.get('rule-providers', {})

        analysis = {
            'proxy_providers': [],
            'rule_providers': [],
            'proxy_provider_count': len(proxy_providers),
            'rule_provider_count': len(rule_providers)
        }

        # 分析 proxy providers
        for name, config in proxy_providers.items():
            analysis['proxy_providers'].append({
                'name': name,
                'type': config.get('type', 'http'),
                'path': config.get('path', ''),
                'url': config.get('url', ''),
                'interval': config.get('interval', 86400)
            })

        # 分析 rule providers
        for name, config in rule_providers.items():
            analysis['rule_providers'].append({
                'name': name,
                'type': config.get('type', 'http'),
                'behavior': config.get('behavior', 'domain'),
                'path': config.get('path', ''),
                'url': config.get('url', ''),
                'interval': config.get('interval', 86400)
            })

        return analysis

    def generate_env_variables(self, provider_count: int) -> List[str]:
        """
        根据 provider 数量生成环境变量名称
        """
        if provider_count == 0:
            return []
        elif provider_count == 1:
            return ['EN_KEY']
        else:
            return [f'EN_KEY{i}' for i in range(1, provider_count + 1)]

    def generate_conf(self, yaml_path: Path, output_path: Path,
                      config_type: str = 'main_router') -> Dict:
        """
        生成 .conf 配置文件
        """
        self.logger.info(f"Generating conf for: {yaml_path.name}")

        # 加载 YAML 配置
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)

        # 分析 providers
        analysis = self.analyze_providers(yaml_config)

        # 生成环境变量
        env_vars = self.generate_env_variables(analysis['proxy_provider_count'])

        # 模板变量
        template_vars = {
            'config_name': yaml_path.stem,
            'config_type': config_type,
            'proxy_providers': analysis['proxy_providers'],
            'rule_providers': analysis['rule_providers'],
            'proxy_groups': yaml_config.get('proxy-groups', []),
            'rules': yaml_config.get('rules', []),
            'env_variables': env_vars,
            'provider_count': analysis['proxy_provider_count'],
            'yaml_download_url': (
                f'https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/processed_configs/{yaml_path.name}'
            )
        }

        # 选择模板
        if config_type == 'smart':
            template_name = 'smart.conf.j2'
        elif config_type == 'bypass_router':
            template_name = 'bypass.conf.j2'
        else:
            template_name = 'main.conf.j2'

        # 渲染模板
        template = self.jinja_env.get_template(template_name)
        rendered = template.render(**template_vars)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered)

        self.logger.info(f"Generated conf: {output_path}")

        return {
            'config_name': yaml_path.stem,
            'env_variables': env_vars,
            'provider_count': analysis['proxy_provider_count']
        }

    def generate_batch(self, yaml_dir: Path, output_dir: Path,
                       config_types: List[str] = None) -> List[Dict]:
        """
        批量生成 .conf 文件
        """
        if config_types is None:
            config_types = ['main_router']

        output_dir.mkdir(parents=True, exist_ok=True)

        results = []

        for yaml_file in yaml_dir.glob('*.yaml'):
            for config_type in config_types:
                try:
                    suffix = '' if config_type == 'main_router' else f'-{config_type}'
                    output_file = output_dir / f"{yaml_file.stem}{suffix}.conf"

                    result = self.generate_conf(yaml_file, output_file, config_type)
                    result['output_file'] = str(output_file)
                    result['config_type'] = config_type

                    results.append(result)

                except Exception as e:
                    self.logger.error(f"Failed to generate {yaml_file.name}: {e}")

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate OpenClash .conf files')
    parser.add_argument('yaml_dir', type=Path, help='Directory with stripped YAML files')
    parser.add_argument('output_dir', type=Path, help='Output directory for .conf files')
    parser.add_argument('--templates', type=Path, default=Path('templates'),
                        help='Templates directory')
    parser.add_argument('--types', nargs='+',
                        choices=['main_router', 'bypass_router', 'smart'],
                        default=['main_router'],
                        help='Config types to generate')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if not args.templates.exists():
        print(f"❌ Template directory not found: {args.templates}")
        return 1

    generator = ConfGenerator(args.templates)
    results = generator.generate_batch(args.yaml_dir, args.output_dir, args.types)

    print("\n" + "=" * 60)
    print("Generation Results")
    print("=" * 60)

    for result in results:
        print(f"\n📄 {result['config_name']} ({result['config_type']})")
        print(f"   Required variables: {', '.join(result['env_variables'])}")
        print(f"   Provider count: {result['provider_count']}")
        print(f"   Output: {result['output_file']}")

    print(f"\n✅ Total generated: {len(results)} files")

    return 0


if __name__ == '__main__':
    sys.exit(main())
