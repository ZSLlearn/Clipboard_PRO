#!/usr/bin/env python3
"""
主窗口模块
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QLineEdit, QCheckBox,
    QMenu, QSystemTrayIcon, QMessageBox, QApplication, QDialog
)
from PyQt6.QtGui import QAction, QFont, QColor, QPalette, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from src.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 定义信号，用于触发UI更新
    update_ui_signal = pyqtSignal()
    
    def __init__(self, storage, monitor, config=None):
        """初始化
        
        Args:
            storage: 存储实例
            monitor: 剪贴板监控器
            config: 配置实例
        """
        super().__init__()
        self.storage = storage
        self.monitor = monitor
        self.config = config
        self.selected_items = set()
        self.is_closing = False  # 添加关闭标志
        
        # 连接信号到槽
        self.update_ui_signal.connect(self.load_records)
        
        # 注册为观察者
        self.storage.add_observer(self)
        
        # 初始化UI
        self.init_ui()
        
        # 初始化系统托盘
        self.init_tray()
        
        # 初始化全局快捷键
        self.init_hotkey()
        
        # 加载记录
        self.load_records()
    
    def get_system_theme_colors(self):
        """获取系统主题颜色
        
        Returns:
            (背景色, 选中色, 文本色) 元组
        """
        palette = QApplication.palette()
        
        # 获取窗口背景色
        window_color = palette.color(QPalette.ColorRole.Window)
        
        # 获取高亮色（选中色）
        highlight_color = palette.color(QPalette.ColorRole.Highlight)
        
        # 获取文本色
        text_color = palette.color(QPalette.ColorRole.WindowText)
        
        return window_color, highlight_color, text_color
    
    def init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle('剪贴板管理 - Windows 11')
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)
        
        # 设置窗口图标
        import sys
        import os
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 主布局
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)
        
        # 左侧筛选栏
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_panel.setFixedWidth(200)
        
        # 搜索框
        search_label = QLabel('搜索')
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('输入关键词')
        self.search_edit.textChanged.connect(self.load_records)
        
        # 类型筛选
        type_label = QLabel('类型筛选')
        self.type_all_btn = QPushButton('全部')
        self.type_text_btn = QPushButton('文本')
        self.type_file_btn = QPushButton('文件')
        self.type_image_btn = QPushButton('图片')
        
        # 清空按钮
        self.clear_btn = QPushButton('清空历史')
        self.clear_btn.clicked.connect(self.confirm_clear)
        
        # 设置按钮
        self.settings_btn = QPushButton('设置')
        self.settings_btn.clicked.connect(self.show_settings)
        
        # 添加到左侧布局
        left_layout.addWidget(search_label)
        left_layout.addWidget(self.search_edit)
        left_layout.addSpacing(20)
        left_layout.addWidget(type_label)
        left_layout.addWidget(self.type_all_btn)
        left_layout.addWidget(self.type_text_btn)
        left_layout.addWidget(self.type_file_btn)
        left_layout.addWidget(self.type_image_btn)
        left_layout.addSpacing(20)
        left_layout.addWidget(self.clear_btn)
        left_layout.addWidget(self.settings_btn)
        left_layout.addStretch()
        
        # 右侧记录列表
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 记录列表
        self.records_list = QListWidget()
        self.records_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.records_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # 优化滚动体验
        self.records_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.records_list.setHorizontalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.records_list.verticalScrollBar().setSingleStep(20)  # 设置单次滚动步长
        
        # 底部操作栏
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        
        self.copy_btn = QPushButton('复制到剪贴板')
        self.delete_btn = QPushButton('删除选中')
        self.select_all_btn = QPushButton('全选')
        
        # 连接信号
        self.type_all_btn.clicked.connect(lambda: self.load_records(filter_type=None, search_term=self.search_edit.text()))
        self.type_text_btn.clicked.connect(lambda: self.load_records(filter_type='text', search_term=self.search_edit.text()))
        self.type_file_btn.clicked.connect(lambda: self.load_records(filter_type='file', search_term=self.search_edit.text()))
        self.type_image_btn.clicked.connect(lambda: self.load_records(filter_type='image', search_term=self.search_edit.text()))
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.select_all_btn.clicked.connect(self.select_all)
        
        # 添加到右侧布局
        right_layout.addWidget(self.records_list)
        right_layout.addWidget(bottom_panel)
        bottom_layout.addWidget(self.copy_btn)
        bottom_layout.addWidget(self.delete_btn)
        bottom_layout.addWidget(self.select_all_btn)
        bottom_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
    
    def init_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon()
        
        # 设置托盘图标
        import sys
        import os
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # 如果找不到图标文件，使用默认图标
            try:
                style = QApplication.style()
                if style:
                    from PyQt6.QtWidgets import QStyle
                    self.tray_icon.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
            except Exception:
                pass
        
        # 托盘菜单
        tray_menu = QMenu()
        show_action = QAction('显示窗口', self)
        exit_action = QAction('退出', self)
        
        show_action.triggered.connect(self.show)
        exit_action.triggered.connect(self.quit_application)  # 修改为调用quit_application
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        
        # 连接托盘图标点击事件（单击显示窗口）
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def on_tray_icon_activated(self, reason):
        """托盘图标被激活
        
        Args:
            reason: 激活原因
        """
        # 单击托盘图标时显示窗口
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def init_hotkey(self):
        """初始化全局快捷键"""
        try:
            import win32api
            import win32con
            import win32gui
            
            # 尝试不同的热键ID
            for hotkey_id in range(1, 10):
                try:
                    # 注册全局热键 Ctrl+Alt+V
                    if win32gui.RegisterHotKey(None, hotkey_id, win32con.MOD_CONTROL | win32con.MOD_ALT, ord('V')):
                        self.hotkey_id = hotkey_id
                        print(f"成功注册热键 Ctrl+Alt+V，ID: {hotkey_id}")
                        break
                except Exception as e:
                    print(f"尝试注册热键 ID {hotkey_id} 时出错: {e}")
            else:
                # 如果所有ID都失败，尝试其他热键组合
                try:
                    # 尝试 Ctrl+Shift+V
                    if win32gui.RegisterHotKey(None, 1, win32con.MOD_CONTROL | win32con.MOD_SHIFT, ord('V')):
                        self.hotkey_id = 1
                        print("成功注册热键 Ctrl+Shift+V")
                    else:
                        print("无法注册任何热键")
                        return
                except:
                    print("无法注册任何热键")
                    return
            
            # 创建消息循环来监听热键
            def hotkey_callback(hwnd, msg, wparam, lparam):
                if msg == win32con.WM_HOTKEY and wparam == self.hotkey_id:
                    self.toggle_window()
                return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
            
            # 注册窗口类
            try:
                wc = win32gui.WNDCLASS()
                # 尝试设置属性
                try:
                    # 类型忽略：PyWNDCLASS属性赋值
                    wc.lpszClassName = "HotkeyListener"  # type: ignore
                    wc.lpfnWndProc = hotkey_callback  # type: ignore
                except Exception:
                    # 如果属性赋值失败，使用其他方式
                    pass
                
                class_atom = win32gui.RegisterClass(wc)
                
                # 创建窗口
                import win32api
                hinst = win32api.GetModuleHandle(None)
                self.hwnd = win32gui.CreateWindow(
                    class_atom, "Hotkey Listener", 0, 0, 0, 0, 0,
                    0, 0, hinst, None
                )
            except Exception as e:
                print(f"创建热键监听器窗口时出错: {e}")
                return
            
            # 启动消息循环
            import threading
            def message_loop():
                while True:
                    try:
                        win32gui.PumpWaitingMessages()
                        import time
                        time.sleep(0.1)
                    except:
                        break
            
            self.message_thread = threading.Thread(target=message_loop)
            self.message_thread.daemon = True
            self.message_thread.start()
            
        except Exception as e:
            print(f"设置全局快捷键时出错: {e}")
    
    def toggle_window(self):
        """切换窗口显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def show_settings(self):
        """显示设置对话框"""
        if self.config is None:
            QMessageBox.warning(self, '警告', '配置未初始化')
            return
        
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 更新存储配置
            self.storage.update_config(self.config)
            # 重新加载记录
            self.load_records()
            QMessageBox.information(self, '成功', '设置已保存')


    
    def load_records(self, filter_type=None, search_term=None):
        """加载记录
        
        Args:
            filter_type: 过滤类型
            search_term: 搜索关键词
        """
        # 获取搜索词
        if search_term is None:
            search_term = self.search_edit.text()
        
        # 获取记录
        records = self.storage.get_records(
            filter_type=filter_type
        )
        
        # 搜索过滤
        if search_term:
            records = [r for r in records if search_term.lower() in r['content'].lower()]
        
        # 清空列表
        self.records_list.clear()
        self.selected_items.clear()
        
        # 添加记录
        for record in records:
            print(f"添加记录: {record['content'][:50]}..." if len(record['content']) > 50 else f"添加记录: {record['content']}")
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, record)
            
            # 创建自定义widget
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(10)
            
            # 创建复选框
            checkbox = QCheckBox()
            checkbox.setChecked(record['id'] in self.selected_items)
            checkbox.stateChanged.connect(lambda state, rid=record['id']: self._on_checkbox_changed(rid, state))
            
            # 创建内容区域
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(5)
            
            # 标题
            title = QLabel(self._get_record_title(record))
            title.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Medium))
            
            # 内容预览
            if record['type'] == 'image':
                # 为图片创建图片预览
                preview = self._create_image_preview(record['content'], record['id'])
            else:
                # 为文本和文件创建可折叠文本预览
                preview = self._create_collapsible_text_preview(record['content'], record['id'])
            
            # 时间戳
            # 格式化时间戳显示
            timestamp_str = record['timestamp']
            # 处理旧格式的时间戳（ISO格式，如2026-02-17T23:16:56.337378）
            if 'T' in timestamp_str and '.' in timestamp_str:
                # 转换为新格式：2026-02-17 23:16:56
                timestamp_str = timestamp_str.replace('T', ' ').split('.')[0]
            timestamp = QLabel(timestamp_str)
            timestamp.setFont(QFont('Microsoft YaHei', 8))
            timestamp.setStyleSheet('color: #666666')
            
            # 添加到内容布局
            content_layout.addWidget(title)
            content_layout.addWidget(preview)
            content_layout.addWidget(timestamp)
            
            # 添加到主布局
            layout.addWidget(checkbox)
            layout.addWidget(content_widget, 1)
            
            # 创建包含分割线的容器widget
            container_widget = QWidget()
            container_layout = QVBoxLayout(container_widget)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            # 添加主要内容widget
            container_layout.addWidget(widget)
            
            # 添加分割线
            separator = QWidget()
            separator.setFixedHeight(1)
            separator.setStyleSheet("background-color: #CCCCCC;")
            container_layout.addWidget(separator)
            
            # 先添加item到list，再设置item widget
            self.records_list.addItem(item)
            # 强制计算widget大小
            container_widget.adjustSize()
            # 设置item大小
            item.setSizeHint(container_widget.sizeHint())
            # 设置item widget
            self.records_list.setItemWidget(item, container_widget)
            print(f"记录已添加，item大小: {item.sizeHint()}")
    
    def _get_record_title(self, record):
        """获取记录标题
        
        Args:
            record: 记录
            
        Returns:
            标题
        """
        if record['type'] == 'text':
            return '文本'
        elif record['type'] == 'file':
            return '文件'
        elif record['type'] == 'image':
            return '图片'
        return '未知'
    
    def _get_record_preview(self, record):
        """获取记录预览
        
        Args:
            record: 记录
            
        Returns:
            预览文本
        """
        if record['type'] == 'image':
            return '[图片] ' + record['content']
        
        content = record['content']
        if len(content) > 100:
            return content[:100] + '...'
        return content
    
    def _create_collapsible_text_preview(self, content, record_id=None):
        """创建可折叠的文本预览
        
        Args:
            content: 文本内容
            record_id: 记录ID（用于检测选中状态）
            
        Returns:
            可折叠文本预览widget
        """
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        from PyQt6.QtCore import Qt
        
        # 创建主widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # 创建折叠状态的预览
        preview_text = content[:100] + '...' if len(content) > 100 else content
        preview_label = QLabel(preview_text)
        preview_label.setFont(QFont('Microsoft YaHei', 9))
        preview_label.setWordWrap(True)
        preview_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        preview_label.setCursor(Qt.CursorShape.IBeamCursor)  # 设置工字形光标
        preview_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        preview_label.customContextMenuRequested.connect(lambda pos: self.show_text_context_menu(pos, content))
        
        # 创建展开状态的完整文本
        full_text_label = QLabel(content)
        full_text_label.setFont(QFont('Microsoft YaHei', 9))
        full_text_label.setWordWrap(True)
        full_text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        full_text_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        full_text_label.setCursor(Qt.CursorShape.IBeamCursor)  # 设置工字形光标
        full_text_label.setVisible(False)  # 默认隐藏
        full_text_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        full_text_label.customContextMenuRequested.connect(lambda pos: self.show_text_context_menu(pos, content))
        
        # 创建展开/收起按钮
        toggle_button = QPushButton('展开' if len(content) > 100 else '')
        toggle_button.setFont(QFont('Microsoft YaHei', 8))
        toggle_button.setStyleSheet('color: #0066CC; border: none; padding: 0;')
        toggle_button.setVisible(len(content) > 100)  # 只有长文本才显示按钮
        
        # 按钮点击事件
        def toggle_text():
            if full_text_label.isVisible():
                # 收起
                full_text_label.setVisible(False)
                preview_label.setVisible(True)
                toggle_button.setText('展开')
            else:
                # 展开
                full_text_label.setVisible(True)
                preview_label.setVisible(False)
                toggle_button.setText('收起')
            
            # 获取records_list的实际可用宽度（减去滚动条和边距）
            available_width = self.records_list.viewport().width() - 20  # 减去左右边距
            
            # 确保有最小宽度
            if available_width < 100:
                available_width = 100
            
            # 设置标签宽度
            preview_label.setMinimumWidth(available_width)
            preview_label.setMaximumWidth(available_width)
            full_text_label.setMinimumWidth(available_width)
            full_text_label.setMaximumWidth(available_width)
            
            # 强制标签重新计算大小
            preview_label.adjustSize()
            full_text_label.adjustSize()
            
            # 获取当前显示的标签
            active_label = full_text_label if full_text_label.isVisible() else preview_label
            
            # 获取标签的实际高度（使用sizeHint获取建议大小）
            label_height = active_label.sizeHint().height()
            
            # 计算需要的总高度（标签高度 + 标题 + 时间戳 + 按钮 + 边距）
            total_height = label_height + 60  # 60像素用于标题、时间戳、按钮和边距
            
            # 重新计算并设置item大小
            # 遍历所有item找到对应的记录
            for i in range(self.records_list.count()):
                item = self.records_list.item(i)
                if item:
                    item_record = item.data(Qt.ItemDataRole.UserRole)
                    if item_record and item_record['id'] == record_id:
                        # 设置item大小
                        new_size = item.sizeHint()
                        new_size.setWidth(available_width)
                        new_size.setHeight(total_height)
                        item.setSizeHint(new_size)
                        
                        # 强制QListWidget更新布局
                        self.records_list.updateGeometry()
                        self.records_list.doItemsLayout()  # 强制重新布局所有item
                        self.records_list.repaint()
                        break
        
        toggle_button.clicked.connect(toggle_text)
        
        # 添加到布局
        main_layout.addWidget(preview_label)
        main_layout.addWidget(full_text_label)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(toggle_button)
        main_layout.addLayout(button_layout)
        
        return main_widget
    
    def _create_image_preview(self, image_path, record_id=None):
        """创建图片预览
        
        Args:
            image_path: 图片路径
            record_id: 记录ID（用于检测选中状态）
            
        Returns:
            图片预览widget
        """
        import os
        from PyQt6.QtGui import QPixmap, QPalette
        from PyQt6.QtCore import Qt
        
        # 创建一个widget来容纳图片
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        # 获取系统主题颜色
        bg_color, highlight_color, text_color = self.get_system_theme_colors()
        
        # 检查是否选中
        is_selected = record_id in self.selected_items if record_id else False
        
        # 设置widget背景色
        try:
            if is_selected:
                image_widget.setStyleSheet(f"background-color: {highlight_color.name()}; border: none; border-radius: 0px;")
            else:
                # 移除边框，只保留背景色
                image_widget.setStyleSheet(f"background-color: {bg_color.name()}; border: none; border-radius: 0px;")
        except Exception as e:
            print(f"设置图片预览样式时出错: {e}")
            # 使用默认样式
            image_widget.setStyleSheet("background-color: transparent; border: none; border-radius: 0px;")
        
        # 检查图片文件是否存在
        if os.path.exists(image_path):
            try:
                # 加载图片
                pixmap = QPixmap(image_path)
                
                # 缩放图片到合适的大小（最大宽度200px）
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        200, 
                        200, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # 创建图片标签
                    image_label = QLabel()
                    image_label.setPixmap(scaled_pixmap)
                    image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    image_label.setMinimumSize(200, 150)
                    image_label.setMaximumSize(200, 150)
                    
                    # 添加到布局
                    image_layout.addWidget(image_label)
                else:
                    # 图片加载失败，显示错误信息
                    error_label = QLabel('[图片加载失败]')
                    error_label.setStyleSheet('color: red;')
                    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    image_layout.addWidget(error_label)
            except Exception as e:
                # 图片处理出错，显示错误信息
                error_label = QLabel(f'[图片错误: {str(e)}]')
                error_label.setStyleSheet('color: red;')
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                image_layout.addWidget(error_label)
        else:
            # 图片文件不存在，显示路径
            path_label = QLabel(f'[图片文件不存在]\n{image_path}')
            path_label.setStyleSheet('color: #666666;')
            path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            path_label.setWordWrap(True)
            image_layout.addWidget(path_label)
        
        return image_widget
    
    def handle_item_click(self, item):
        """处理项目点击
        
        Args:
            item: 列表项
        """
        pass
    
    def _on_checkbox_changed(self, record_id, state):
        """复选框状态变化处理
        
        Args:
            record_id: 记录ID
            state: 复选框状态
        """
        if state == 2:  # Qt.CheckState.Checked
            self.selected_items.add(record_id)
        else:  # Qt.CheckState.Unchecked
            if record_id in self.selected_items:
                self.selected_items.remove(record_id)
    
    def show_text_context_menu(self, position, content):
        """显示文本内容的右键菜单
        
        Args:
            position: 位置
            content: 文本内容
        """
        # 获取发送信号的控件
        sender = self.sender()
        if sender:
            # 检查是否有选中的文本
            selected_text = sender.selectedText()
            if selected_text:
                # 如果有选中的文本，使用选中的文本
                copy_content = selected_text
            else:
                # 如果没有选中的文本，使用全部内容
                copy_content = content
            # 将局部坐标转换为全局坐标
            global_pos = sender.mapToGlobal(position)
        else:
            copy_content = content
            global_pos = position
        
        menu = QMenu()
        copy_action = QAction('复制文本', self)
        select_all_action = QAction('选择全部', self)
        
        copy_action.triggered.connect(lambda: self.copy_text_to_clipboard(copy_content))
        select_all_action.triggered.connect(lambda: self.select_all_text(content))
        
        menu.addAction(copy_action)
        menu.addAction(select_all_action)
        menu.exec(global_pos)
    
    def copy_text_to_clipboard(self, content):
        """复制文本到剪贴板
        
        Args:
            content: 文本内容
        """
        import pyperclip
        pyperclip.copy(content)
    
    def select_all_text(self, content):
        """选择全部文本
        
        Args:
            content: 文本内容
        """
        pass  # QLabel的文本选择由系统自动处理
    
    def show_context_menu(self, position):
        """显示上下文菜单
        
        Args:
            position: 位置
        """
        item = self.records_list.itemAt(position)
        if not item:
            return
        
        record = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        copy_action = QAction('复制到剪贴板', self)
        delete_action = QAction('删除', self)
        
        copy_action.triggered.connect(lambda: self.copy_record(record))
        delete_action.triggered.connect(lambda: self.delete_record(record))
        
        menu.addAction(copy_action)
        menu.addAction(delete_action)
        menu.exec(self.records_list.mapToGlobal(position))
    
    def copy_record(self, record):
        """复制记录到剪贴板
        
        Args:
            record: 记录
        """
        import win32clipboard
        import win32con
        import ctypes
        from ctypes import wintypes
        
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            
            if record['type'] == 'image':
                from PIL import Image
                import io
                
                img = Image.open(record['content'])
                output = io.BytesIO()
                img.save(output, format='BMP')
                dib_data = output.getvalue()[14:]
                win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
                
            elif record['type'] == 'file':
                files = record['content'].split('\n')
                
                class DROPFILES(ctypes.Structure):
                    _fields_ = [
                        ('pFiles', wintypes.DWORD),
                        ('pt', wintypes.POINT),
                        ('fNC', wintypes.BOOL),
                        ('fWide', wintypes.BOOL)
                    ]
                
                drop_files = DROPFILES()
                drop_files.pFiles = ctypes.sizeof(DROPFILES)
                drop_files.pt.x = 0
                drop_files.pt.y = 0
                drop_files.fNC = False
                drop_files.fWide = True
                
                dropfiles_bytes = ctypes.string_at(ctypes.byref(drop_files), ctypes.sizeof(DROPFILES))
                
                file_list = '\0'.join(files) + '\0\0'
                file_bytes = file_list.encode('utf-16-le')
                
                hdrop_data = dropfiles_bytes + file_bytes
                win32clipboard.SetClipboardData(win32con.CF_HDROP, hdrop_data)
                
            else:
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, record['content'])
                
        except Exception as e:
            print(f"复制到剪贴板时出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
    
    def delete_record(self, record):
        """删除记录
        
        Args:
            record: 记录
        """
        self.storage.delete_record(record['id'])
        self.load_records()
    
    def copy_to_clipboard(self):
        """复制选中到剪贴板"""
        if not self.selected_items:
            QMessageBox.warning(self, '警告', '请先选择要复制的记录')
            return
        
        # 获取第一个选中的记录
        for i in range(self.records_list.count()):
            item = self.records_list.item(i)
            if not item:
                continue
            
            try:
                record = item.data(Qt.ItemDataRole.UserRole)
                if record and record['id'] in self.selected_items:
                    self.copy_record(record)
                    break
            except Exception:
                pass
    
    def delete_selected(self):
        """删除选中"""
        if not self.selected_items:
            QMessageBox.warning(self, '警告', '请先选择要删除的记录')
            return
        
        if QMessageBox.question(self, '确认', f'确定要删除选中的 {len(self.selected_items)} 条记录吗？') == QMessageBox.StandardButton.Yes:
            self.storage.delete_multiple(self.selected_items)
            self.load_records()
    
    def select_all(self):
        """全选"""
        self.selected_items.clear()
        
        for i in range(self.records_list.count()):
            item = self.records_list.item(i)
            if not item:
                continue
            
            try:
                record = item.data(Qt.ItemDataRole.UserRole)
                if record:
                    self.selected_items.add(record['id'])
                    
                    # 获取 widget 中的复选框并设置选中状态
                    widget = self.records_list.itemWidget(item)
                    if widget:
                        # widget 是 container_widget，它的第一个子元素是主 widget
                        main_widget = widget.findChild(QWidget)
                        if main_widget:
                            # 主 widget 的第一个子元素是复选框
                            checkbox = main_widget.findChild(QCheckBox)
                            if checkbox:
                                checkbox.blockSignals(True)
                                checkbox.setChecked(True)
                                checkbox.blockSignals(False)
            except Exception as e:
                print(f"全选时出错: {e}")
    
    def confirm_clear(self):
        """确认清空"""
        if QMessageBox.question(self, '确认', '确定要清空所有历史记录吗？此操作不可恢复。') == QMessageBox.StandardButton.Yes:
            self.storage.clear_all()
            self.load_records()
            QMessageBox.information(self, '提示', '已清空所有历史记录')
    
    def on_storage_change(self):
        """更新界面（观察者方法）"""
        # 此方法用于响应存储变化的通知
        print("收到存储变化通知，正在发送UI更新信号...")
        # 发出信号，触发UI更新（会在主线程中执行）
        self.update_ui_signal.emit()
        print("UI更新信号已发送")
    
    def quit_application(self):
        """完全退出应用程序"""
        print("正在退出应用程序...")
        self.is_closing = True
        
        # 停止剪贴板监控
        if hasattr(self.monitor, 'stop_monitoring'):
            self.monitor.stop_monitoring()
            print("剪贴板监控已停止")
        
        # 注销热键
        try:
            import win32gui
            if hasattr(self, 'hotkey_id'):
                win32gui.UnregisterHotKey(None, self.hotkey_id)
                print("热键已注销")
        except Exception as e:
            print(f"注销热键时出错: {e}")
        
        # 根据配置决定是否清除数据
        if self.config and self.config.get_clear_data_on_exit():
            print("正在清理数据...")
            self.storage.clear_all()
            print("所有记录和临时文件已删除")
        else:
            print("保留历史记录和临时数据")
        
        # 隐藏托盘图标
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
            print("托盘图标已隐藏")
        
        # 退出应用
        QApplication.quit()
        print("应用程序已退出")
    
    def closeEvent(self, a0):
        """关闭事件
        
        Args:
            a0: 事件
        """
        # 如果正在关闭，直接关闭
        if self.is_closing:
            print("正在关闭窗口...")
            a0.accept()
            return
        
        # 否则最小化到托盘
        try:
            if a0:
                a0.ignore()
        except Exception:
            pass
        self.hide()
        print("窗口已最小化到托盘")
        QMessageBox.information(self, '提示', '软件已最小化到系统托盘')