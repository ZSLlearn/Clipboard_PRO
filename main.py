#!/usr/bin/env python3
"""
Windows 11 剪贴板管理软件 - 主入口
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSharedMemory
from src.main_window import MainWindow
from src.clipboard_monitor import ClipboardMonitor
from src.storage import Storage


def check_single_instance():
    """检查是否已有实例运行
    
    Returns:
        bool: True表示已有实例运行，False表示没有
    """
    shared_memory = QSharedMemory('ClipboardPRO_SingleInstance')
    
    if shared_memory.attach():
        # 如果能够attach，说明已有实例运行
        shared_memory.detach()
        return True
    else:
        # 如果无法attach，说明没有实例运行
        return False


def get_resource_path(relative_path):
    """获取资源文件的绝对路径
    
    Args:
        relative_path: 相对路径
        
    Returns:
        资源文件的绝对路径
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def main():
    """主函数"""
    # 检查单实例
    if check_single_instance():
        print("程序已在运行中，请勿重复启动")
        return
    
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 设置应用图标
    icon_path = get_resource_path('icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 初始化存储
    storage = Storage()
    
    # 创建剪贴板监控器
    monitor = ClipboardMonitor(storage)
    
    # 创建主窗口
    window = MainWindow(storage, monitor)
    
    # 启动监控
    monitor.start_monitoring()
    
    # 显示窗口
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()