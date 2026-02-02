#!/usr/bin/env python3
"""
YAML Stripper - 提取並精簡 Mihomo YAML 配置文件
只保留: rule-providers, rules, proxy-groups, proxy-providers 和锚點
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Set
import logging


class YAMLStripper:
    """YAML 配置精簡處理器"""

    KEEP_KEYS = {
        'proxy-providers',
        'proxy-groups',
        'rule-providers',
        'rules'
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.anchors = {}

    def extract_anchors(self, yaml_content: str) -> Dict[str, str]:
        anchors = {}
        anchor_pattern = r'^(\s*)&(\w+)\s*(.+)$'

        for line in yaml_content.split('\n'):
            match = re.match(anchor_pattern, line)
            if match:
                indent, anchor_name, content = match.groups()
                anchors[anchor_name] = f"{indent}&{anchor_name} {content}"
                self.logger.debug(f"Found anchor: {anchor_name}")

        return anchors

    def find_referenced_anchors(self, content: Dict) -> Set[str]:
        referenced = set()
        content_str = yaml.dump(content)
        matches = re.findall(r'\*(\w+)', content_str)
        referenced.update(matches)
        return referenced

    def strip_yaml(self, yaml_path: Path) -> Dict[str, Any]:
        self.logger.info(f"Processing: {yaml_path.name}")

        with open(yaml_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        self.anchors = self.extract_anchors(raw_content)

        try:
            full_config = yaml.safe_load(raw_content)
        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML: {e}")
            return {}

        stripped_config = {}
        for key in self.KEEP_KEYS:
            if key in full_config:
                stripped_config[key] = full_config[key]

        referenced = self.find_referenced_anchors(stripped_config)

        stripped_config['_anchors'] = {
            name: self.anchors[name]
            for name in referenced
            if name in self.anchors
        }

        return stripped_config

    def count_providers(self, config: Dict) -> Dict[str, int]:
        return {
            'proxy_providers': len(config.get('proxy-providers', {})),
            'rule_providers': len(config.get('rule-providers', {})),
            'proxy_groups': len(config.get('proxy-groups', [])),
            'rules': len(config.get('rules', []))
        }

    def save_stripped_yaml(self, config: Dict, output_path: Path,
                           include_anchors: bool = True) -> None:

        save_config = {k: v for k, v in config.items() if k != '_anchors'}

        yaml_content = yaml.dump(
            save_config,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )

        if include_anchors and '_anchors' in config:
            anchor_lines = [
                "# ============================================================================",
                "# 锚點定義 (Anchors)",
                "# ============================================================================"
            ]
            anchor_lines.extend(config['_anchors'].values())
            anchor_lines.append("")
            yaml_content = '\n'.join(anchor_lines) + '\n' + yaml_content

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        self.logger.info(f"Saved stripped YAML to: {output_path}")

    def process_directory(self, input_dir: Path, output_dir: Path) -> List[Dict]:
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)

        for yaml_file in input_dir.glob('*.yaml'):
            try:
                stripped = self.strip_yaml(yaml_file)

                if not stripped:
                    self.logger.warning(f"Skipped empty config: {yaml_file.name}")
                    continue

                counts = self.count_providers(stripped)
                output_file = output_dir / yaml_file.name
                self.save_stripped_yaml(stripped, output_file)

                results.append({
                    'filename': yaml_file.name,
                    'counts': counts,
                    'output': str(output_file)
                })

            except Exception as e:
                self.logger.error(f"Failed to process {yaml_file.name}: {e}")

        return results


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Strip Mihomo YAML configs')
    parser.add_argument('input_dir', type=Path, help='Input directory')
    parser.add_argument('output_dir', type=Path, help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    setup_logging(logging.DEBUG if args.verbose else logging.INFO)

    stripper = YAMLStripper()
    results = stripper.process_directory(args.input_dir, args.output_dir)

    print("\n" + "=" * 60)
    print("Processing Results")
    print("=" * 60)

    for result in results:
        print(f
