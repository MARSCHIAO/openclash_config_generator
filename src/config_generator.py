#!/usr/bin/env python3
"""
OpenClash Config Generator
主配置生成器 - 负责读取配置并生成 .conf 文件
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import yaml
from jinja2 import Environment, FileSystemLoader, Template

from yaml_processor import YAMLProcessor
from utils import ensure_dir, setup_logging, validate_config


class ConfigGenerator:
    """OpenClash 配置生成器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置生成器
        
        Args:
            config_path: 项目配置文件路径
        """
        self.logger = setup_logging()
        self.logger.info("初始化 ConfigGenerator")
        
        # 加载项目配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 验证配置
        if not validate_config(self.config):
            raise ValueError("配置文件验证失败")
        
        # 设置路径
        self.project_root = Path(__file__).parent.parent
        self.template_dir = self.project_root / "templates"
        self.output_dir = self.project_root / self.config['output']['directory']
        self.configs_dir = self.project_root / "configs"
        
        # 确保目录存在
        ensure_dir(self.output_dir)
        ensure_dir(self.configs_dir)
        
        # 初始化 Jinja2 环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 初始化 YAML 处理器
        self.yaml_processor = YAMLProcessor()
        
        self.logger.info("ConfigGenerator 初始化完成")
    
    def generate_all(self) -> None:
        """生成所有配置文件"""
        self.logger.info("开始生成所有配置文件")
        
        for format_config in self.config['output']['formats']:
            try:
                self.generate_config(
                    format_config['name'],
                    format_config['filename'],
                    format_config['description']
                )
            except Exception as e:
                self.logger.error(f"生成配置 {format_config['name']} 失败: {e}")
        
        self.logger.info("所有配置文件生成完成")
    
    def generate_config(self, config_type: str, filename: str, description: str) -> None:
        """
        生成特定类型的配置文件
        
        Args:
            config_type: 配置类型 (main_router, bypass_router等)
            filename: 输出文件名
            description: 配置描述
        """
        self.logger.info(f"生成配置: {config_type} -> {filename}")
        
        # 准备模板变量
        template_vars = self._prepare_template_vars(config_type)
        
        # 选择模板
        template_name = self._get_template_name(config_type)
        template = self.jinja_env.get_template(template_name)
        
        # 渲染模板
        rendered_content = template.render(**template_vars)
        
        # 写入文件
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        self.logger.info(f"配置文件已生成: {output_path}")
    
    def _prepare_template_vars(self, config_type: str) -> Dict:
        """
        准备模板变量
        
        Args:
            config_type: 配置类型
            
        Returns:
            模板变量字典
        """
        # 基础变量
        vars_dict = {
            'config_type': config_type,
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'openclash': self.config['openclash'],
            'downloads': self.config.get('downloads', [])
        }
        
        # 根据配置类型调整参数
        if 'noipv6' in config_type:
            vars_dict['openclash']['ipv6']['enable'] = 0
            vars_dict['openclash']['ipv6']['dns'] = 0
        
        if 'bypass' in config_type:
            vars_dict['openclash']['firewall']['bypass_gateway_compatible'] = 1
            vars_dict['is_bypass'] = True
        else:
            vars_dict['is_bypass'] = False
        
        if 'smart' in config_type:
            vars_dict['openclash']['smart']['auto_switch'] = 1
            vars_dict['is_smart'] = True
            
            if 'lgbm' in config_type:
                vars_dict['openclash']['smart']['enable_lgbm'] = 1
                vars_dict['is_lgbm'] = True
            else:
                vars_dict['openclash']['smart']['enable_lgbm'] = 0
                vars_dict['is_lgbm'] = False
        else:
            vars_dict['openclash']['smart']['auto_switch'] = 0
            vars_dict['is_smart'] = False
            vars_dict['is_lgbm'] = False
        
        return vars_dict
    
    def _get_template_name(self, config_type: str) -> str:
        """
        根据配置类型获取模板名称
        
        Args:
            config_type: 配置类型
            
        Returns:
            模板文件名
        """
        if 'smart' in config_type:
            return 'smart.conf.j2'
        elif 'bypass' in config_type:
            return 'bypass_router.conf.j2'
        else:
            return 'main_router.conf.j2'
    
    def sync_upstream(self) -> None:
        """从上游仓库同步配置文件"""
        self.logger.info("开始同步上游配置")
        
        # 这里可以实现 Git clone/pull 逻辑
        # 或使用 GitHub API 下载文件
        
        # 示例：使用 GitPython
        try:
            from git import Repo
            
            repo_url = f"https://github.com/{self.config['upstream']['repo']}.git"
            branch = self.config['upstream']['branch']
            
            if (self.configs_dir / '.git').exists():
                # 更新现有仓库
                repo = Repo(self.configs_dir)
                origin = repo.remote('origin')
                origin.pull(branch)
                self.logger.info("上游配置已更新")
            else:
                # 克隆新仓库
                Repo.clone_from(repo_url, self.configs_dir, branch=branch)
                self.logger.info("上游配置已克隆")
                
        except ImportError:
            self.logger.warning("GitPython 未安装，跳过 Git 同步")
        except Exception as e:
            self.logger.error(f"同步上游配置失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OpenClash Config Generator')
    parser.add_argument(
        '--type',
        choices=['all', 'main_router', 'bypass_router', 'smart'],
        default='all',
        help='生成的配置类型'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='项目配置文件路径'
    )
    parser.add_argument(
        '--sync',
        action='store_true',
        help='同步上游配置'
    )
    
    args = parser.parse_args()
    
    try:
        generator = ConfigGenerator(args.config)
        
        if args.sync:
            generator.sync_upstream()
        
        if args.type == 'all':
            generator.generate_all()
        else:
            # 根据类型查找对应的配置
            for format_config in generator.config['output']['formats']:
                if args.type in format_config['name']:
                    generator.generate_config(
                        format_config['name'],
                        format_config['filename'],
                        format_config['description']
                    )
        
        print("✅ 配置文件生成成功！")
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
