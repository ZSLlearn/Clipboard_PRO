#!/usr/bin/env python3
"""
配置管理模块 - 负责用户设置的保存和加载
"""

import json
import os


class Config:
    """配置管理类"""
    
    def __init__(self):
        """初始化配置"""
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        self.config = self._load_default_config()
        self._load_config()
    
    def _load_default_config(self):
        """加载默认配置
        
        Returns:
            默认配置字典
        """
        return {
            'max_records': None,
            'max_age_minutes': None,
            'clear_data_on_exit': True
        }
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件时出错: {e}")
    
    def get_max_records(self):
        """获取最大记录条数
        
        Returns:
            最大记录条数，None表示不限制
        """
        return self.config.get('max_records')
    
    def set_max_records(self, max_records):
        """设置最大记录条数
        
        Args:
            max_records: 最大记录条数，None表示不限制
        """
        self.config['max_records'] = max_records
        self._save_config()
    
    def get_max_age_minutes(self):
        """获取最大存留时间（分钟）
        
        Returns:
            最大存留时间（分钟），None表示不限制
        """
        return self.config.get('max_age_minutes')
    
    def set_max_age_minutes(self, max_age_minutes):
        """设置最大存留时间（分钟）
        
        Args:
            max_age_minutes: 最大存留时间（分钟），None表示不限制
        """
        self.config['max_age_minutes'] = max_age_minutes
        self._save_config()
    
    def get_clear_data_on_exit(self):
        """获取退出时是否清除数据
        
        Returns:
            True表示清除，False表示保留
        """
        return self.config.get('clear_data_on_exit', True)
    
    def set_clear_data_on_exit(self, clear_data):
        """设置退出时是否清除数据
        
        Args:
            clear_data: True表示清除，False表示保留
        """
        self.config['clear_data_on_exit'] = clear_data
        self._save_config()
    
    def get_all(self):
        """获取所有配置
        
        Returns:
            配置字典
        """
        return self.config.copy()
