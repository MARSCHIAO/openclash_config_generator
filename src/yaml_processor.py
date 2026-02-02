#!/usr/bin/env python3
"""
YAML Processor
处理 Mihomo YAML 配置文件，提取关键信息
"""

import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path


class YAMLProcessor:
    """YAML 配置文件处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.logger = logging.getLogger(__name__)
    
    def load_yaml(self, file_path: str) -> Dict:
        """
        加载 YAML 文件
        
        Args:
            file_path: YAML 文件路径
            
        Returns:
            解析后的配置字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"成功加载 YAML: {file_path}")
            return config
        except Exception as e:
            self.logger.error(f"加载 YAML 失败: {e}")
            raise
    
    def extract_dns_config(self, config: Dict) -> Dict:
        """
        提取 DNS 配置
        
        Args:
            config: Mihomo 配置字典
            
        Returns:
            DNS 配置字典
        """
        dns = config.get('dns', {})
        
        return {
            'enable': dns.get('enable', True),
            'ipv6': dns.get('ipv6', True),
            'enhanced_mode': dns.get('enhanced-mode', 'fake-ip'),
            'fake_ip_range': dns.get('fake-ip-range', '198.18.0.1/16'),
            'fake_ip_filter': dns.get('fake-ip-filter', []),
            'nameserver': dns.get('nameserver', []),
            'fallback': dns.get('fallback', []),
            'nameserver_policy': dns.get('nameserver-policy', {}),
        }
    
    def extract_proxy_groups(self, config: Dict) -> List[Dict]:
        """
        提取代理组配置
        
        Args:
            config: Mihomo 配置字典
            
        Returns:
            代理组列表
        """
        proxy_groups = config.get('proxy-groups', [])
        
        processed_groups = []
        for group in proxy_groups:
            processed_groups.append({
                'name': group.get('name', ''),
                'type': group.get('type', 'select'),
                'proxies': group.get('proxies', []),
                'url': group.get('url', ''),
                'interval': group.get('interval', 300),
                'tolerance': group.get('tolerance', 50),
            })
        
        return processed_groups
    
    def extract_rules(self, config: Dict) -> List[str]:
        """
        提取规则配置
        
        Args:
            config: Mihomo 配置字典
            
        Returns:
            规则列表
        """
        return config.get('rules', [])
    
    def extract_rule_providers(self, config: Dict) -> Dict:
        """
        提取规则提供者配置
        
        Args:
            config: Mihomo 配置字典
            
        Returns:
            规则提供者字典
        """
        return config.get('rule-providers', {})
    
    def extract_proxy_providers(self, config: Dict) -> Dict:
        """
        提取代理提供者配置
        
        Args:
            config: Mihomo 配置字典
            
        Returns:
            代理提供者字典
        """
        return config.get('proxy-providers', {})
    
    def convert_to_openclash_params(self, config: Dict) -> Dict:
        """
        将 Mihomo 配置转换为 OpenClash 参数
        
        Args:
            config: Mihomo 配置字典
            
        Returns:
            OpenClash 参数字典
        """
        params = {}
        
        # DNS 参数
        dns = config.get('dns', {})
        params['dns_enable'] = 1 if dns.get('enable', True) else 0
        params['dns_ipv6'] = 1 if dns.get('ipv6', True) else 0
        params['dns_enhanced_mode'] = dns.get('enhanced-mode', 'fake-ip')
        params['fake_ip_range'] = dns.get('fake-ip-range', '198.18.0.1/16')
        
        # 基础参数
        params['ipv6'] = 1 if config.get('ipv6', True) else 0
        params['log_level'] = config.get('log-level', 'info')
        params['allow_lan'] = 1 if config.get('allow-lan', True) else 0
        params['mode'] = config.get('mode', 'rule')
        
        # 嗅探参数
        sniffer = config.get('sniffer', {})
        params['sniffer_enable'] = 1 if sniffer.get('enable', False) else 0
        
        # TUN 参数
        tun = config.get('tun', {})
        params['tun_enable'] = 1 if tun.get('enable', False) else 0
        params['tun_stack'] = tun.get('stack', 'system')
        
        return params
    
    def get_config_summary(self, config: Dict) -> Dict:
        """
        获取配置摘要信息
        
        Args:
            config: Mihomo 配置字典
            
        Returns:
            配置摘要字典
        """
        summary = {
            'proxy_groups_count': len(config.get('proxy-groups', [])),
            'rules_count': len(config.get('rules', [])),
            'rule_providers_count': len(config.get('rule-providers', {})),
            'proxy_providers_count': len(config.get('proxy-providers', {})),
            'dns_enabled': config.get('dns', {}).get('enable', True),
            'ipv6_enabled': config.get('ipv6', True),
            'mode': config.get('mode', 'rule'),
        }
        
        return summary
    
    def validate_config(self, config: Dict) -> bool:
        """
        验证配置文件完整性
        
        Args:
            config: Mihomo 配置字典
            
        Returns:
            是否有效
        """
        required_keys = ['proxy-groups', 'rules']
        
        for key in required_keys:
            if key not in config:
                self.logger.warning(f"配置缺少必需的键: {key}")
                return False
        
        return True
    
    def merge_configs(self, configs: List[Dict]) -> Dict:
        """
        合并多个配置文件
        
        Args:
            configs: 配置字典列表
            
        Returns:
            合并后的配置字典
        """
        merged = {
            'proxy-groups': [],
            'rules': [],
            'rule-providers': {},
            'proxy-providers': {},
        }
        
        for config in configs:
            # 合并代理组
            merged['proxy-groups'].extend(config.get('proxy-groups', []))
            
            # 合并规则
            merged['rules'].extend(config.get('rules', []))
            
            # 合并规则提供者
            merged['rule-providers'].update(config.get('rule-providers', {}))
            
            # 合并代理提供者
            merged['proxy-providers'].update(config.get('proxy-providers', {}))
        
        # 去重代理组名称
        seen_names = set()
        unique_groups = []
        for group in merged['proxy-groups']:
            name = group.get('name')
            if name not in seen_names:
                seen_names.add(name)
                unique_groups.append(group)
        merged['proxy-groups'] = unique_groups
        
        # 去重规则
        merged['rules'] = list(dict.fromkeys(merged['rules']))
        
        return merged
    
    def generate_ruby_edit_commands(self, config: Dict) -> List[str]:
        """
        生成 Ruby 编辑命令（用于 OpenClash 覆写）
        
        Args:
            config: Mihomo 配置字典
            
        Returns:
            Ruby 命令列表
        """
        commands = []
        
        # DNS 配置命令
        dns = config.get('dns', {})
        if dns:
            commands.append(
                f'ruby_edit "$CONFIG_FILE" "[\'dns\'][\'enable\']" "{str(dns.get("enable", True)).lower()}"'
            )
            commands.append(
                f'ruby_edit "$CONFIG_FILE" "[\'dns\'][\'ipv6\']" "{str(dns.get("ipv6", True)).lower()}"'
            )
        
        # 代理提供者命令
        proxy_providers = config.get('proxy-providers', {})
        if proxy_providers:
            commands.append(
                'ruby_map_edit "$CONFIG_FILE" "[\'proxy-providers\']" "provider" "[\'url\']" "$EN_KEY"'
            )
        
        return commands


if __name__ == '__main__':
    # 测试代码
    processor = YAMLProcessor()
    
    # 这里可以添加测试逻辑
    print("YAMLProcessor 模块已加载")
