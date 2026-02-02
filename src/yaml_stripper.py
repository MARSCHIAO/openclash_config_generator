#!/usr/bin/env python3
"""
YAML Stripper - 提取并精简 Mihomo YAML 配置文件
只保留: rule-providers, rules, proxy-groups, proxy-providers 和锚点
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Set
import logging


class YAMLStripper:
    """YAML 配置精简处理器"""
    
    # 需要保留的顶级键
    KEEP_KEYS = {
        'proxy-providers',
        'proxy-groups',
        'rule-providers',
        'rules'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.anchors = {}  # 存储提取的锚点
    
    def extract_anchors(self, yaml_content: str) -> Dict[str, str]:
        """
        提取 YAML 文件中的锚点定义
        
        Args:
            yaml_content: YAML 文件内容
            
        Returns:
            锚点字典 {anchor_name: anchor_content}
        """
        anchors = {}
        
        # 匹配锚点定义 (例如: &anchor_name)
        anchor_pattern = r'^(\s*)&(\w+)\s*(.+)$'
        
        for line in yaml_content.split('\n'):
            match = re.match(anchor_pattern, line)
            if match:
                indent, anchor_name, content = match.groups()
                anchors[anchor_name] = f"{indent}&{anchor_name} {content}"
                self.logger.debug(f"Found anchor: {anchor_name}")
        
        return anchors
    
    def find_referenced_anchors(self, content: Dict) -> Set[str]:
        """
        查找被引用的锚点
        
        Args:
            content: YAML 内容字典
            
        Returns:
            被引用的锚点名称集合
        """
        referenced = set()
        content_str = yaml.dump(content)
        
        # 匹配锚点引用 (例如: *anchor_name)
        ref_pattern = r'\*(\w+)'
        matches = re.findall(ref_pattern, content_str)
        
        referenced.update(matches)
        return referenced
    
    def strip_yaml(self, yaml_path: Path) -> Dict[str, Any]:
        """
        精简 YAML 文件，只保留必要的部分
        
        Args:
            yaml_path: YAML 文件路径
            
        Returns:
            精简后的配置字典
        """
        self.logger.info(f"Processing: {yaml_path.name}")
        
        # 读取原始文件
        with open(yaml_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # 提取锚点
        self.anchors = self.extract_anchors(raw_content)
        
        # 解析 YAML
        try:
            full_config = yaml.safe_load(raw_content)
        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML: {e}")
            return {}
        
        # 只保留指定的键
        stripped_config = {}
        for key in self.KEEP_KEYS:
            if key in full_config:
                stripped_config[key] = full_config[key]
        
        # 查找被引用的锚点
        referenced_anchors = self.find_referenced_anchors(stripped_config)
        
        # 保存被引用的锚点
        stripped_config['_anchors'] = {
            name: self.anchors[name]
            for name in referenced_anchors
            if name in self.anchors
        }
        
        return stripped_config
    
    def count_providers(self, config: Dict) -> Dict[str, int]:
        """
        统计 provider 数量
        
        Args:
            config: 配置字典
            
        Returns:
            统计结果 {type: count}
        """
        counts = {
            'proxy_providers': len(config.get('proxy-providers', {})),
            'rule_providers': len(config.get('rule-providers', {})),
            'proxy_groups': len(config.get('proxy-groups', [])),
            'rules': len(config.get('rules', []))
        }
        
        return counts
    
    def save_stripped_yaml(self, config: Dict, output_path: Path, 
                          include_anchors: bool = True) -> None:
        """
        保存精简后的 YAML 文件
        
        Args:
            config: 精简后的配置字典
            output_path: 输出文件路径
            include_anchors: 是否包含锚点
        """
        # 移除内部使用的 _anchors 键
        save_config = {k: v for k, v in config.items() if k != '_anchors'}
        
        yaml_content = yaml.dump(
            save_config,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )
        
        # 如果需要包含锚点，添加到文件开头
        if include_anchors and '_anchors' in config:
            anchor_lines = [
                "# ============================================================================",
                "# 锚点定义 (Anchors)",
                "# ============================================================================"
            ]
            anchor_lines.extend(config['_anchors'].values())
            anchor_lines.append("")
            
            yaml_content = '\n'.join(anchor_lines) + '\n' + yaml_content
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        self.logger.info(f"Saved stripped YAML to: {output_path}")
    
    def process_directory(self, input_dir: Path, output_dir: Path) -> List[Dict]:
        """
        批量处理目录中的所有 YAML 文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            
        Returns:
            处理结果列表
        """
        results = []
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 处理所有 YAML 文件
        for yaml_file in input_dir.glob('*.yaml'):
            try:
                # 精简配置
                stripped_config = self.strip_yaml(yaml_file)
                
                if not stripped_config:
                    self.logger.warning(f"Skipped empty config: {yaml_file.name}")
                    continue
                
                # 统计信息
                counts = self.count_providers(stripped_config)
                
                # 保存精简后的文件
                output_file = output_dir / yaml_file.name
                self.save_stripped_yaml(stripped_config, output_file)
                
                # 记录结果
                results.append({
                    'filename': yaml_file.name,
                    'counts': counts,
                    'output': str(output_file)
                })
                
            except Exception as e:
                self.logger.error(f"Failed to process {yaml_file.name}: {e}")
        
        return results


def setup_logging(level=logging.INFO):
    """设置日志"""
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
    
    # 设置日志
    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    
    # 处理文件
    stripper = YAMLStripper()
    results = stripper.process_directory(args.input_dir, args.output_dir)
    
    # 显示结果
    print("\n" + "="*60)
    print("Processing Results")
    print("="*60)
    
    for result in results:
        print(f"\n📄 {result['filename']}")
        print(f"   Proxy Providers: {result['counts']['proxy_providers']}")
        print(f"   Rule Providers: {result['counts']['rule_providers']}")
        print(f"   Proxy Groups: {result['counts']['proxy_groups']}")
        print(f"   Rules: {result['counts']['rules']}")
    
    print(f"\n✅ Total processed: {len(results)} files")
