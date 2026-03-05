#!/usr/bin/env python3
"""
设置对话框模块
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QGroupBox, QButtonGroup, QRadioButton, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config, parent=None):
        """初始化
        
        Args:
            config: 配置实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.config = config
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('设置')
        self.setMinimumSize(400, 400)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 最大记录条数设置
        records_group = QGroupBox('剪贴板保留条数')
        records_layout = QVBoxLayout(records_group)
        
        self.records_button_group = QButtonGroup(self)
        
        records_options = [
            (10, '10条'),
            (20, '20条'),
            (30, '30条'),
            (40, '40条'),
            (None, '不限制')
        ]
        
        for value, label in records_options:
            radio = QRadioButton(label)
            self.records_button_group.addButton(radio)
            radio.setProperty('value', value)
            records_layout.addWidget(radio)
        
        main_layout.addWidget(records_group)
        
        # 存留时间设置
        time_group = QGroupBox('剪贴板存留时间')
        time_layout = QVBoxLayout(time_group)
        
        self.time_button_group = QButtonGroup(self)
        
        time_options = [
            (5, '5分钟'),
            (10, '10分钟'),
            (20, '20分钟'),
            (30, '30分钟'),
            (40, '40分钟'),
            (60, '60分钟'),
            (None, '不限制')
        ]
        
        for value, label in time_options:
            radio = QRadioButton(label)
            self.time_button_group.addButton(radio)
            radio.setProperty('value', value)
            time_layout.addWidget(radio)
        
        main_layout.addWidget(time_group)
        
        # 退出时清除数据设置
        exit_group = QGroupBox('退出设置')
        exit_layout = QVBoxLayout(exit_group)
        
        self.clear_data_checkbox = QCheckBox('退出软件时清除所有历史记录和临时数据')
        exit_layout.addWidget(self.clear_data_checkbox)
        
        main_layout.addWidget(exit_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton('确定')
        self.ok_button.clicked.connect(self.accept_settings)
        
        self.cancel_button = QPushButton('取消')
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def load_current_settings(self):
        """加载当前设置"""
        # 加载最大记录条数
        max_records = self.config.get_max_records()
        for button in self.records_button_group.buttons():
            value = button.property('value')
            if value == max_records:
                button.setChecked(True)
                break
        
        # 加载存留时间
        max_age_minutes = self.config.get_max_age_minutes()
        for button in self.time_button_group.buttons():
            value = button.property('value')
            if value == max_age_minutes:
                button.setChecked(True)
                break
        
        # 加载退出时清除数据设置
        self.clear_data_checkbox.setChecked(self.config.get_clear_data_on_exit())
    
    def accept_settings(self):
        """接受设置"""
        # 获取选中的最大记录条数
        selected_records_button = self.records_button_group.checkedButton()
        if selected_records_button:
            max_records = selected_records_button.property('value')
            self.config.set_max_records(max_records)
        
        # 获取选中的存留时间
        selected_time_button = self.time_button_group.checkedButton()
        if selected_time_button:
            max_age_minutes = selected_time_button.property('value')
            self.config.set_max_age_minutes(max_age_minutes)
        
        # 保存退出时清除数据设置
        self.config.set_clear_data_on_exit(self.clear_data_checkbox.isChecked())
        
        self.accept()
