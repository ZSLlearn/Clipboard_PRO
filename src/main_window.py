#!/usr/bin/env python3
"""
主窗口模块
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QLineEdit, QCheckBox,
    QMenu, QSystemTrayIcon, QMessageBox, QApplication, QDialog, QSizePolicy, QScrollArea
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
        self.current_filter = None  # 当前筛选类型
        
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
    
    def _get_border_color(self):
        """获取边框颜色（根据主题自适应）
        
        Returns:
            边框颜色
        """
        palette = QApplication.palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        
        # 根据背景色计算边框颜色
        if window_color.lightness() < 128:
            return QColor(80, 80, 80)  # 深色模式使用深灰色边框
        else:
            return QColor(204, 204, 204)  # 浅色模式使用浅灰色边框
    
    def _get_disabled_color(self):
        """获取禁用状态颜色（根据主题自适应）
        
        Returns:
            禁用状态颜色
        """
        palette = QApplication.palette()
        text_color = palette.color(QPalette.ColorRole.WindowText)
        
        # 根据文本色计算禁用颜色
        if text_color.lightness() < 128:
            return QColor(150, 150, 150)  # 深色模式使用较亮的灰色
        else:
            return QColor(153, 153, 153)  # 浅色模式使用较暗的灰色
    
    def init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle('ClipboardPRO')
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
        
        # 搜索区域
        search_area = QWidget()
        search_layout = QVBoxLayout(search_area)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        
        # 搜索输入框（带清除按钮）
        search_input_container = QWidget()
        search_input_layout = QHBoxLayout(search_input_container)
        search_input_layout.setContentsMargins(0, 0, 0, 0)
        search_input_layout.setSpacing(0)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('搜索剪贴板历史...')
        
        # 添加搜索防抖
        self.search_timer = None
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        
        # 获取系统主题颜色
        bg_color, highlight_color, text_color = self.get_system_theme_colors()
        
        self.search_edit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {self._get_border_color()};
                border-radius: 4px;
                padding: 8px 30px 8px 10px;
                background-color: {bg_color.name()};
                color: {text_color.name()};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {highlight_color.name()};
            }}
        """)
        
        # 清除按钮
        self.clear_search_btn = QPushButton('×')
        self.clear_search_btn.setFixedSize(20, 20)
        self.clear_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        disabled_color = self._get_disabled_color()
        self.clear_search_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                color: {disabled_color.name()};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {text_color.name()};
            }}
        """)
        self.clear_search_btn.clicked.connect(self.clear_search)
        self.clear_search_btn.setVisible(False)
        
        search_input_layout.addWidget(self.search_edit)
        
        # 将清除按钮放在输入框内右侧
        self.search_edit.setLayout(QHBoxLayout())
        self.search_edit.layout().setContentsMargins(0, 0, 5, 0)
        self.search_edit.layout().addStretch()
        self.search_edit.layout().addWidget(self.clear_search_btn)
        
        # 类型筛选标签（横向排列）
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(15)
        
        # 创建筛选标签按钮
        self.filter_buttons = {}
        filter_options = [
            (None, '全部'),
            ('text', '文本'),
            ('file', '文件'),
            ('image', '图片')
        ]
        
        for filter_type, label in filter_options:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty('filter_type', filter_type)
            btn.clicked.connect(lambda checked, ft=filter_type: self.on_filter_clicked(ft))
            self.filter_buttons[filter_type] = btn
            filter_layout.addWidget(btn)
        
        filter_layout.addStretch()
        
        search_layout.addWidget(search_input_container)
        search_layout.addWidget(filter_container)
        
        # 初始化筛选按钮样式
        self._update_filter_buttons_style(None)
        
        # 清空按钮
        self.clear_btn = QPushButton('清空历史')
        self.clear_btn.clicked.connect(self.confirm_clear)
        
        # 设置按钮
        self.settings_btn = QPushButton('设置')
        self.settings_btn.clicked.connect(self.show_settings)
        
        # 添加到左侧布局
        left_layout.addWidget(search_area)
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
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.select_all_btn.clicked.connect(self.toggle_select_all)
        
        # 初始隐藏复制和删除按钮
        self.copy_btn.setVisible(False)
        self.delete_btn.setVisible(False)
        
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
            self.toggle_window()
    
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
                    # 在主线程中调用 toggle_window
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, self.toggle_window)
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
                
                # 创建隐藏窗口来监听热键（不使用消息窗口，因为消息窗口无法正确接收消息）
                import win32api
                hinst = win32api.GetModuleHandle(None)
                self.hwnd = win32gui.CreateWindowEx(
                    win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_LAYERED,  # 扩展样式
                    class_atom, "Hotkey Listener", 
                    0,  # 无样式
                    0, 0, 1, 1,  # 位置和大小（最小化）
                    None,  # 不使用 HWND_MESSAGE，使用普通隐藏窗口
                    0, hinst, None
                )
                # 确保窗口完全不可见
                win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
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
        if self.isVisible() and not self.isMinimized():
            # 如果窗口可见且未最小化，则隐藏到托盘
            self.hide()
        else:
            # 如果窗口隐藏或最小化，则显示窗口
            self.show()
            self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
            self.raise_()
            self.activateWindow()
            self.setFocus()
    
    def show_settings(self):
        """显示设置对话框"""
        if self.config is None:
            return
        
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 更新存储配置
            self.storage.update_config(self.config)
            # 重新加载记录
            self.load_records()
    
    def clear_search(self):
        """清空搜索框"""
        self.search_edit.clear()
        self.clear_search_btn.setVisible(False)
    
    def on_filter_clicked(self, filter_type):
        """筛选标签点击处理
        
        Args:
            filter_type: 筛选类型
        """
        # 只有当筛选类型真正改变时才执行操作
        if self.current_filter != filter_type:
            # 更新按钮样式
            self._update_filter_buttons_style(filter_type)
            # 加载记录
            self.load_records(filter_type=filter_type, search_term=self.search_edit.text())
    
    def _on_search_text_changed(self):
        """搜索文本变化处理（带防抖）"""
        # 清除之前的定时器
        if self.search_timer:
            self.search_timer.stop()
        
        # 创建新的定时器，300ms后执行搜索
        from PyQt6.QtCore import QTimer
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.load_records(filter_type=self.current_filter))
        self.search_timer.start(300)
    
    def _update_filter_buttons_style(self, active_filter):
        """更新筛选按钮样式
        
        Args:
            active_filter: 当前激活的筛选类型
        """
        bg_color, highlight_color, text_color = self.get_system_theme_colors()
        disabled_color = self._get_disabled_color()
        
        for filter_type, btn in self.filter_buttons.items():
            if filter_type == active_filter:
                # 选中状态：高亮色文字 + 下划线
                btn.setStyleSheet(f"""
                    QPushButton {{
                        border: none;
                        background: transparent;
                        color: {highlight_color.name()};
                        font-size: 13px;
                        font-weight: bold;
                        padding: 5px 0px;
                        text-decoration: underline;
                    }}
                    QPushButton:hover {{
                        text-decoration: underline;
                    }}
                """)
            else:
                # 未选中状态：禁用色文字
                btn.setStyleSheet(f"""
                    QPushButton {{
                        border: none;
                        background: transparent;
                        color: {disabled_color.name()};
                        font-size: 13px;
                        padding: 5px 0px;
                    }}
                    QPushButton:hover {{
                        color: {highlight_color.name()};
                    }}
                """)


    
    def load_records(self, filter_type=None, search_term=None):
        """加载记录
        
        Args:
            filter_type: 过滤类型
            search_term: 搜索关键词
        """
        # 保存当前筛选类型（包括 None 值）
        self.current_filter = filter_type
        
        # 获取搜索词
        if search_term is None:
            search_term = self.search_edit.text()
        
        # 控制清除按钮显示/隐藏
        if hasattr(self, 'clear_search_btn'):
            self.clear_search_btn.setVisible(bool(search_term))
        
        # 获取记录
        records = self.storage.get_records(
            filter_type=filter_type
        )
        
        # 搜索过滤
        if search_term:
            records = [r for r in records if search_term.lower() in r['content'].lower()]
        
        # 禁用更新以减少闪烁
        self.records_list.setUpdatesEnabled(False)
        
        # 清空列表
        self.records_list.clear()
        self.selected_items.clear()
        
        # 添加记录
        for record in records:
            print(f"添加记录: {record['content'][:50]}..." if len(record['content']) > 50 else f"添加记录: {record['content']}")
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, record)
            
            # 创建自定义 widget（设置父对象以避免闪烁）
            widget = QWidget(self.records_list)
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(10)
            
            # 创建复选框
            checkbox = QCheckBox(widget)
            checkbox.setChecked(record['id'] in self.selected_items)
            checkbox.stateChanged.connect(lambda state, rid=record['id']: self._on_checkbox_changed(rid, state))
            
            # 获取系统主题颜色
            bg_color, highlight_color, text_color = self.get_system_theme_colors()
            disabled_color = self._get_disabled_color()
            
            # 创建类型标识
            type_label = QLabel(self._get_record_title(record), widget)
            type_label.setFont(QFont('Microsoft YaHei', 9))
            type_label.setMinimumWidth(80)
            type_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            type_label.setStyleSheet(f'color: {text_color.name()}; font-weight: bold;')
            
            # 创建内容区域
            content_widget = QWidget(widget)
            content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(5)
            
            # 内容预览
            if record['type'] == 'image':
                # 为图片创建图片预览
                preview = self._create_image_preview(record['content'], record['id'])
            else:
                # 为文本和文件创建可折叠文本预览
                preview = self._create_collapsible_text_preview(record['content'], record['id'], record['type'])
            
            # 时间戳
            # 格式化时间戳显示
            timestamp_str = record['timestamp']
            # 处理旧格式的时间戳（ISO格式，如2026-02-17T23:16:56.337378）
            if 'T' in timestamp_str and '.' in timestamp_str:
                # 转换为新格式：2026-02-17 23:16:56
                timestamp_str = timestamp_str.replace('T', ' ').split('.')[0]
            timestamp = QLabel(timestamp_str)
            timestamp.setFont(QFont('Microsoft YaHei', 8))
            timestamp.setStyleSheet(f'color: {disabled_color.name()}')
            
            # 添加到内容布局
            content_layout.addWidget(preview)
            content_layout.addWidget(timestamp)
            
            # 添加到主布局
            layout.addWidget(checkbox)
            layout.addWidget(type_label)
            layout.addWidget(content_widget, 1)
            
            # 创建包含分割线的容器 widget（设置父对象以避免闪烁）
            container_widget = QWidget(self.records_list)
            container_layout = QVBoxLayout(container_widget)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            # 添加主要内容 widget
            container_layout.addWidget(widget)
            
            # 添加分割线
            separator = QWidget(container_widget)
            separator.setFixedHeight(1)
            border_color = self._get_border_color()
            separator.setStyleSheet(f"background-color: {border_color.name()};")
            container_layout.addWidget(separator)
            
            # 先添加item到list，再设置item widget
            self.records_list.addItem(item)
            # 强制计算widget大小
            container_widget.adjustSize()
            # 获取建议大小
            size_hint = container_widget.sizeHint()
            # 设置item大小（根据内容自适应，最小高度60）
            size_hint.setHeight(max(size_hint.height(), 60))
            item.setSizeHint(size_hint)
            # 设置item widget
            self.records_list.setItemWidget(item, container_widget)
            print(f"记录已添加，item大小: {item.sizeHint()}")
        
        # 恢复更新
        self.records_list.setUpdatesEnabled(True)
    
    def _get_record_title(self, record):
        """获取记录标题
        
        Args:
            record: 记录
            
        Returns:
            标题（带图标）
        """
        if record['type'] == 'text':
            return '📝 文本'
        elif record['type'] == 'file':
            return '📁 文件'
        elif record['type'] == 'image':
            return '🖼️ 图片'
        return '❓ 未知'
    
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
    
    def _create_collapsible_text_preview(self, content, record_id=None, record_type='text'):
        """创建可折叠的文本预览
        
        Args:
            content: 文本内容
            record_id: 记录ID（用于检测选中状态）
            record_type: 记录类型（text 或 file）
            
        Returns:
            可折叠文本预览widget
        """
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollArea
        from PyQt6.QtCore import Qt
        import html
        import os
        
        # 获取系统主题颜色
        bg_color, highlight_color, text_color = self.get_system_theme_colors()
        disabled_color = self._get_disabled_color()
        
        # 获取当前搜索词
        search_term = self.search_edit.text().strip() if hasattr(self, 'search_edit') else ''
        
        # 创建主widget
        main_widget = QWidget()
        main_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # 如果是文件类型，显示文件名和路径
        if record_type == 'file':
            # 提取文件名
            filename = os.path.basename(content)
            
            # 创建文件名标签（加粗）
            filename_label = QLabel(filename)
            filename_label.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
            filename_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            filename_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            filename_label.setCursor(Qt.CursorShape.IBeamCursor)
            filename_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            filename_label.customContextMenuRequested.connect(lambda pos: self.show_text_context_menu(pos, content))
            
            # 创建文件路径标签
            path_label = QLabel(content)
            path_label.setFont(QFont('Microsoft YaHei', 8))
            path_label.setStyleSheet(f'color: {disabled_color.name()};')
            path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            path_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            path_label.setCursor(Qt.CursorShape.IBeamCursor)
            path_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            path_label.customContextMenuRequested.connect(lambda pos: self.show_text_context_menu(pos, content))
            
            # 添加到布局
            main_layout.addWidget(filename_label)
            main_layout.addWidget(path_label)
        else:
            # 文本类型，显示文本内容
            preview_text = content[:100] + '...' if len(content) > 100 else content
            
            # 如果有搜索词，进行高亮处理
            if search_term and len(content) <= 100:
                preview_text = self._highlight_search_terms(content, search_term)
            elif search_term and len(content) > 100:
                preview_text = self._highlight_search_terms(content[:100] + '...', search_term)
            
            preview_label = QLabel()
            preview_label.setFont(QFont('Microsoft YaHei', 9))
            preview_label.setWordWrap(True)
            preview_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            preview_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            preview_label.setCursor(Qt.CursorShape.IBeamCursor)  # 设置工字形光标
            preview_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            preview_label.customContextMenuRequested.connect(lambda pos: self.show_text_context_menu(pos, content))
            preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            preview_label.setMinimumHeight(20)
            
            # 设置文本，使用 setText 确保正确换行
            if search_term:
                # 有高亮时使用 HTML
                preview_label.setText(preview_text)
            else:
                # 无高亮时使用纯文本，确保正确换行
                preview_label.setText(content if len(content) <= 100 else content[:100] + '...')
            
            # 添加到布局
            main_layout.addWidget(preview_label)
            
            # 创建显示全部按钮
            show_full_button = QPushButton('点击显示全部')
            show_full_button.setFont(QFont('Microsoft YaHei', 8))
            show_full_button.setCursor(Qt.CursorShape.PointingHandCursor)
            show_full_button.setMinimumHeight(20)  # 设置最小高度
            show_full_button.setMaximumHeight(25)  # 设置最大高度
            show_full_button.setMinimumWidth(80)  # 设置最小宽度，确保按钮不会被压缩
            show_full_button.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Fixed
            )  # 设置大小策略，固定大小
            show_full_button.setStyleSheet(f"""
                QPushButton {{
                    color: {highlight_color.name()};
                    border: none;
                    padding: 2px 0;
                    background: transparent;
                }}
                QPushButton:hover {{
                    text-decoration: underline;
                }}
            """)
            show_full_button.setVisible(len(content) > 100)  # 只有长文本才显示按钮
            
            # 按钮点击事件 - 弹出对话框显示全部文本
            def show_full_text():
                self.show_full_text_dialog(content, search_term)
            
            show_full_button.clicked.connect(show_full_text)
            
            # 创建按钮的水平布局，确保左对齐
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.addWidget(show_full_button)
            button_layout.addStretch()  # 添加弹性空间，确保按钮左对齐
            main_layout.addLayout(button_layout)
        
        # 设置主widget的最小高度，确保按钮始终可见
        main_widget.setMinimumHeight(60)
        
        return main_widget
    
    def _highlight_search_terms(self, text, search_term):
        """高亮搜索词
        
        Args:
            text: 原始文本
            search_term: 搜索词
            
        Returns:
            带高亮标签的HTML文本
        """
        if not search_term:
            return text
        
        # 获取系统主题颜色
        bg_color, highlight_color, text_color = self.get_system_theme_colors()
        
        # 计算高亮背景色（半透明）
        highlight_bg = QColor(highlight_color)
        highlight_bg.setAlpha(50)  # 设置透明度为50%
        
        # 转义HTML特殊字符
        import html
        escaped_text = html.escape(text)
        escaped_search = html.escape(search_term)
        
        # 使用正则表达式进行不区分大小写的替换
        import re
        pattern = re.compile(f'({re.escape(escaped_search)})', re.IGNORECASE)
        
        # 替换为高亮标签
        highlighted_text = pattern.sub(
            f'<span style="background-color: {highlight_bg.name()}; color: {text_color.name()}; padding: 1px 2px; border-radius: 2px;">\\1</span>',
            escaped_text
        )
        
        return highlighted_text
    
    def show_full_text_dialog(self, content, search_term=''):
        """显示全部文本的对话框
        
        Args:
            content: 文本内容
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
        from PyQt6.QtCore import Qt
        
        # 获取系统主题颜色
        bg_color, highlight_color, text_color = self.get_system_theme_colors()
        border_color = self._get_border_color()
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle('查看全部文本')
        dialog.setMinimumSize(600, 400)
        
        # 主布局
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 文本编辑框
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont('Microsoft YaHei', 10))
        
        # 如果有搜索词，使用带高亮的HTML
        if search_term:
            highlighted_content = self._highlight_search_terms(content, search_term)
            text_edit.setHtml(f'<div style="color: {text_color.name()};">{highlighted_content}</div>')
        else:
            text_edit.setPlainText(content)
        
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {border_color.name()};
                border-radius: 4px;
                background-color: {bg_color.name()};
                color: {text_color.name()};
                padding: 10px;
            }}
        """)
        layout.addWidget(text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        copy_button = QPushButton('复制文本')
        copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {highlight_color.name()};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {highlight_color.lighter(110).name()};
            }}
        """)
        copy_button.clicked.connect(lambda: self.copy_text_to_clipboard(content))
        
        close_button = QPushButton('关闭')
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 根据主题计算按钮背景色
        if bg_color.lightness() < 128:
            btn_bg_color = QColor(60, 60, 60)
            btn_hover_color = QColor(80, 80, 80)
        else:
            btn_bg_color = QColor(245, 245, 245)
            btn_hover_color = QColor(224, 224, 224)
        
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg_color.name()};
                color: {text_color.name()};
                border: 1px solid {border_color.name()};
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover_color.name()};
            }}
        """)
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addWidget(copy_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # 设置为非模态对话框，允许操作其他窗口
        dialog.setModal(False)
        # 显示对话框
        dialog.show()
    
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
                    image_label.setCursor(Qt.CursorShape.PointingHandCursor)  # 设置手形光标
                    image_label.setToolTip('点击查看大图')  # 添加提示
                    
                    # 添加鼠标点击事件
                    image_label.mousePressEvent = lambda event: self.show_image_preview_dialog(image_path)
                    
                    # 添加到布局
                    image_layout.addWidget(image_label)
                else:
                    # 图片加载失败，显示错误信息
                    error_label = QLabel('[图片加载失败]')
                    error_color = QColor(255, 100, 100)  # 错误色（红色系）
                    error_label.setStyleSheet(f'color: {error_color.name()};')
                    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    image_layout.addWidget(error_label)
            except Exception as e:
                # 图片处理出错，显示错误信息
                error_label = QLabel(f'[图片错误: {str(e)}]')
                error_color = QColor(255, 100, 100)  # 错误色（红色系）
                error_label.setStyleSheet(f'color: {error_color.name()};')
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                image_layout.addWidget(error_label)
        else:
            # 图片文件不存在，显示路径
            path_label = QLabel(f'[图片文件不存在]\n{image_path}')
            disabled_color = self._get_disabled_color()
            path_label.setStyleSheet(f'color: {disabled_color.name()};')
            path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            path_label.setWordWrap(True)
            image_layout.addWidget(path_label)
        
        return image_widget
    
    def show_image_preview_dialog(self, image_path):
        """显示图片预览对话框
        
        Args:
            image_path: 图片路径
        """
        import os
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollArea
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        
        # 获取系统主题颜色
        bg_color, highlight_color, text_color = self.get_system_theme_colors()
        border_color = self._get_border_color()
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle('图片预览')
        dialog.setMinimumSize(400, 300)
        
        # 主布局
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {border_color.name()};
                border-radius: 4px;
                background-color: {bg_color.name()};
            }}
        """)
        
        # 创建图片标签
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 加载图片
        if os.path.exists(image_path):
            try:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 缩放图片到合适的大小（最大宽度800px）
                    scaled_pixmap = pixmap.scaled(
                        800,
                        800,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    image_label.setPixmap(scaled_pixmap)
                else:
                    image_label.setText('[图片加载失败]')
                    image_label.setStyleSheet(f'color: {QColor(255, 100, 100).name()};')
            except Exception as e:
                image_label.setText(f'[图片错误: {str(e)}]')
                image_label.setStyleSheet(f'color: {QColor(255, 100, 100).name()};')
        else:
            image_label.setText('[图片文件不存在]')
            image_label.setStyleSheet(f'color: {self._get_disabled_color().name()};')
        
        scroll_area.setWidget(image_label)
        layout.addWidget(scroll_area)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        copy_button = QPushButton('复制图片')
        copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {highlight_color.name()};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {highlight_color.lighter(110).name()};
            }}
        """)
        copy_button.clicked.connect(lambda: self.copy_image_to_clipboard(image_path))
        
        close_button = QPushButton('关闭')
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 根据主题计算按钮背景色
        if bg_color.lightness() < 128:
            btn_bg_color = QColor(60, 60, 60)
            btn_hover_color = QColor(80, 80, 80)
        else:
            btn_bg_color = QColor(245, 245, 245)
            btn_hover_color = QColor(224, 224, 224)
        
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg_color.name()};
                color: {text_color.name()};
                border: 1px solid {border_color.name()};
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover_color.name()};
            }}
        """)
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addWidget(copy_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # 设置为非模态对话框，允许操作其他窗口
        dialog.setModal(False)
        # 显示对话框
        dialog.show()
    
    def copy_image_to_clipboard(self, image_path):
        """复制图片到剪贴板
        
        Args:
            image_path: 图片路径
        """
        import win32clipboard
        import win32con
        from PIL import Image
        import io
        
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            
            img = Image.open(image_path)
            output = io.BytesIO()
            img.save(output, format='BMP')
            dib_data = output.getvalue()[14:]
            win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
            
        except Exception as e:
            print(f"复制图片到剪贴板时出错: {e}")
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
    
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
        
        # 更新按钮可见性
        has_selection = len(self.selected_items) > 0
        self.copy_btn.setVisible(has_selection)
        self.delete_btn.setVisible(has_selection)
        
        # 更新全选按钮文本
        self._update_select_all_button_text()
    
    def _update_select_all_button_text(self):
        """根据当前选中状态更新全选按钮文本"""
        total_items = self.records_list.count()
        if total_items == 0:
            self.select_all_btn.setText('全选')
            # 没有记录时隐藏所有操作按钮
            self.copy_btn.setVisible(False)
            self.delete_btn.setVisible(False)
            return
        
        # 如果全部选中，显示"取消全选"，否则显示"全选"
        if len(self.selected_items) == total_items:
            self.select_all_btn.setText('取消全选')
        else:
            self.select_all_btn.setText('全选')
        
        # 更新按钮可见性
        has_selection = len(self.selected_items) > 0
        self.copy_btn.setVisible(has_selection)
        self.delete_btn.setVisible(has_selection)
    
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
            return
        
        # 如果只选中了一个记录，直接复制
        if len(self.selected_items) == 1:
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
        else:
            # 多选复制模式：合并文本内容
            texts = []
            for i in range(self.records_list.count()):
                item = self.records_list.item(i)
                if not item:
                    continue
                
                try:
                    record = item.data(Qt.ItemDataRole.UserRole)
                    if record and record['id'] in self.selected_items:
                        if record['type'] == 'text':
                            texts.append(record['content'])
                        elif record['type'] == 'file':
                            texts.append(record['content'])
                except Exception:
                    pass
            
            if texts:
                # 合并文本，用换行符分隔
                combined_text = '\n'.join(texts)
                self.copy_text_to_clipboard(combined_text)
    
    def delete_selected(self):
        """删除选中"""
        if not self.selected_items:
            return
        
        # 直接执行删除
        self.storage.delete_multiple(self.selected_items)
        # 清空选中集合
        self.selected_items.clear()
        # 重新加载记录
        self.load_records()
        # 更新按钮可见性
        self.copy_btn.setVisible(False)
        self.delete_btn.setVisible(False)
    

    
    def toggle_select_all(self):
        """切换全选/取消全选"""
        # 检查当前是否已全部选中
        total_items = self.records_list.count()
        if total_items == 0:
            return
        
        # 如果当前已选中的数量等于总数，则执行取消全选，否则执行全选
        if len(self.selected_items) == total_items:
            self.deselect_all()
        else:
            self.select_all()
    
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
        
        # 更新按钮文本（通过统一的方法）
        self._update_select_all_button_text()
    
    def deselect_all(self):
        """取消全选"""
        self.selected_items.clear()
        
        for i in range(self.records_list.count()):
            item = self.records_list.item(i)
            if not item:
                continue
            
            try:
                # 获取 widget 中的复选框并设置未选中状态
                widget = self.records_list.itemWidget(item)
                if widget:
                    main_widget = widget.findChild(QWidget)
                    if main_widget:
                        checkbox = main_widget.findChild(QCheckBox)
                        if checkbox:
                            checkbox.blockSignals(True)
                            checkbox.setChecked(False)
                            checkbox.blockSignals(False)
            except Exception as e:
                print(f"取消全选时出错: {e}")
        
        # 更新按钮文本（通过统一的方法）
        self._update_select_all_button_text()
    
    def confirm_clear(self):
        """确认清空"""
        self.storage.clear_all()
        self.load_records()
    
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
    
    def resizeEvent(self, event):
        """窗口大小变化事件
        
        Args:
            event: 事件
        """
        super().resizeEvent(event)
        # 延迟更新 item 大小，确保布局已稳定
        from PyQt6.QtCore import QTimer
        # 取消之前的定时器，避免重复触发
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._update_items_size)
        self._resize_timer.start(100)
    
    def _update_items_size(self):
        """更新所有 item 的大小"""
        # 获取列表宽度
        list_width = self.records_list.viewport().width()
        
        for i in range(self.records_list.count()):
            item = self.records_list.item(i)
            widget = self.records_list.itemWidget(item)
            if widget:
                # 设置 widget 宽度为列表宽度减去滚动条宽度
                widget.setFixedWidth(list_width - 20)
                # 更新布局
                widget.updateGeometry()
                # 获取建议大小
                size_hint = widget.sizeHint()
                # 设置 item 大小
                item.setSizeHint(size_hint)
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        # Ctrl+C复制选中内容
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.copy_to_clipboard()
        # Delete键删除选中内容
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        # Esc键隐藏窗口
        elif event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
    
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