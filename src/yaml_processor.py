#!/usr/bin/env python3
"""
YAML Processor - 精简 YAML 配置文件
"""
import yaml
import re
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Optional


class YAMLProcessor:
    KEEP_KEYS = {
        'proxy-providers',
        'proxy-groups',
        'rule-providers',
        'rules'
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.anchors = {}

    def extract_anchors(self, content: str) -> Dict[str, str]:
        """提取 YAML 锚点"""
        anchors = {}
        pattern = r'^(\s*)&(\w+)\s+(.+)$'
        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                indent, name, value = match.groups()
                anchors[name] = f"{indent}&{name} {value}"
        return anchors

    def find_referenced_anchors(self, content: Any) -> Set[str]:
        """查找引用的锚点"""
        text = yaml.dump(content, allow_unicode=True)
        return set(re.findall(r'\*(\w+)', text))

    def process_file(self, yaml_path: Path) -> Optional[Dict]:
        """处理单个 YAML 文件"""
        self.logger.info(f"Processing: {yaml_path}")
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            self.anchors = self.extract_anchors(raw_content)
            config = yaml.safe_load(raw_content)
            
            if not config:
                return None

            # 只保留必要的键
            stripped = {k: config[k] for k in self.KEEP_KEYS if k in config}
            
            if not stripped:
                self.logger.warning(f"No valid keys in {yaml_path}")
                return None

            # 处理锚点
            referenced = self.find_referenced_anchors(stripped)
            if referenced and self.anchors:
                stripped['_anchors'] = {
                    name: self.anchors[name]
                    for name in referenced if name in self.anchors
                }

            # 添加元数据
            stripped['_meta'] = {
                'source': str(yaml_path),
                'proxy_providers': len(stripped.get('proxy-providers', {})),
                'rule_providers': len(stripped.get('rule-providers', {})),
                'proxy_groups': len(stripped.get('proxy-groups', [])),
                'rules': len(stripped.get('rules', []))
            }
            
            return stripped
            
        except Exception as e:
            self.logger.error(f"Error processing {yaml_path}: {e}")
            return None

    def save_file(self, config: Dict, output_path: Path):
        """保存处理后的文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 分离元数据
        meta = config.pop('_meta', {})
        anchors = config.pop('_anchors', {})
        
        lines = []
        
        # 写入头部注释
        lines.append(f"# Processed: {meta.get('source', 'unknown')}")
        lines.append(f"# Providers: {meta.get('proxy_providers', 0)} proxy, {meta.get('rule_providers', 0)} rule")
        lines.append("")
        
        # 写入锚点
        if anchors:
            lines.extend([
                "# ============================================================================",
                "# Anchors",
                "# ============================================================================"
            ])
            for name in sorted(anchors.keys()):
                lines.append(anchors[name])
            lines.append("")
        
        # 写入配置
        yaml_content = yaml.dump(
            config, 
            default_flow_style=False, 
            allow_unicode=True,
            sort_keys=False
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n' + yaml_content)
        
        self.logger.info(f"Saved: {output_path}")

    def process_directory(self, input_dir: Path, output_dir: Path, 
                         recursive: bool = False) -> List[Dict]:
        """处理目录"""
        results = []
        pattern = '**/*.yaml' if recursive else '*.yaml'
        
        yaml_files = list(input_dir.glob(pattern))
        self.logger.info(f"Found {len(yaml_files)} YAML files")
        
        for yaml_file in yaml_files:
            if not yaml_file.is_file():
                continue
                
            try:
                rel_path = yaml_file.relative_to(input_dir)
                output_file = output_dir / rel_path
                
                config = self.process_file(yaml_file)
                if config:
                    self.save_file(config, output_file)
                    results.append({
                        'input': str(yaml_file),
                        'output': str(output_file),
                        'meta': config.get('_meta', {})
                    })
            except Exception as e:
                self.logger.error(f"Failed to process {yaml_file}: {e}")
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Process YAML configs')
    parser.add_argument('--input', '-i', type=Path, required=True)
    parser.add_argument('--output', '-o', type=Path, required=True)
    parser.add_argument('--recursive', '-r', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    
    args = parser.parse_args()
    
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )
    
    if not args.input.exists():
        print(f"❌ Input directory not found: {args.input}")
        return 1
    
    processor = YAMLProcessor()
    results = processor.process_directory(args.input, args.output, args.recursive)
    
    print(f"\n✅ Successfully processed: {len(results)} files")
    return 0


if __name__ == '__main__':
    exit(main())
