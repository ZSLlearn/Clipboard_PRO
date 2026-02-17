#!/usr/bin/env python3
"""
剪贴板监控模块
"""

import time
import threading
import os
import sys
from datetime import datetime

# 尝试导入win32相关模块
try:
    import win32clipboard
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("警告: 无法导入win32clipboard和win32con模块")


class ClipboardMonitor:
    """剪贴板监控器"""
    
    def __init__(self, storage):
        """初始化
        
        Args:
            storage: 存储实例
        """
        self.storage = storage
        self.running = False
        self.last_content = None
        self.monitor_thread = None
        
        # 设置临时文件目录
        self.temp_dir = self._get_temp_dir()
        print(f"临时文件目录: {self.temp_dir}")
        
        # 确保临时目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _get_temp_dir(self):
        """获取临时文件目录
        
        Returns:
            临时文件目录路径
        """
        # 如果是打包后的exe，使用exe所在目录
        if getattr(sys, 'frozen', False):
            # PyInstaller打包后的路径
            exe_dir = os.path.dirname(sys.executable)
            return os.path.join(exe_dir, 'temp_images')
        else:
            # 开发环境，使用项目根目录
            return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_images')
    
    def start_monitoring(self):
        """开始监控"""
        print(f"开始监控剪贴板，WIN32_AVAILABLE: {WIN32_AVAILABLE}")
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("剪贴板监控线程已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """监控循环"""
        print("监控循环已启动")
        counter = 0
        while self.running:
            try:
                counter += 1
                if counter % 10 == 0:  # 每10次循环打印一次日志
                    print(f"监控循环运行中... 第 {counter} 次检查")
                self._check_clipboard()
            except Exception as e:
                print(f"监控剪贴板时出错: {e}")
            time.sleep(0.5)  # 500ms检查一次
    
    def _check_clipboard(self):
        """检查剪贴板变化"""
        if not WIN32_AVAILABLE:
            print("WIN32不可用，跳过剪贴板检查")
            return
        
        try:
            # 确保win32clipboard和win32con可用
            global win32clipboard, win32con
            print("开始检查剪贴板...")
            
            # 打开剪贴板
            win32clipboard.OpenClipboard()
            print("成功打开剪贴板")
            
            # 检查是否有文本
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                print("检测到文本格式 (CF_UNICODETEXT)")
                try:
                    content = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                    print(f"获取到文本内容: {content[:50]}..." if len(content) > 50 else f"获取到文本内容: {content}")
                    # 调试比较逻辑
                    print(f"当前内容类型: {type(content)}, 值: {content}")
                    print(f"上次内容类型: {type(self.last_content)}, 值: {self.last_content}")
                    print(f"内容比较结果: {content != self.last_content}")
                    
                    if content != self.last_content:
                        print(f"文本内容已变化，上次内容: {self.last_content[:50]}..." if self.last_content and len(str(self.last_content)) > 50 else f"文本内容已变化，上次内容: {self.last_content}")
                        self._handle_new_content('text', content)
                        self.last_content = content
                        print("已处理新的文本内容")
                    else:
                        print("文本内容未变化")
                except Exception as e:
                    print(f"读取文本内容时出错: {e}")
            # 尝试使用其他文本格式
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                print("检测到文本格式 (CF_TEXT)")
                try:
                    content = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                    # 尝试解码
                    try:
                        content = content.decode('gbk')
                    except:
                        try:
                            content = content.decode('utf-8')
                        except:
                            pass
                    print(f"获取到文本内容: {content[:50]}..." if len(content) > 50 else f"获取到文本内容: {content}")
                    if content != self.last_content:
                        self._handle_new_content('text', content)
                        self.last_content = content
                        print("已处理新的文本内容")
                    else:
                        print("文本内容未变化")
                except Exception as e:
                    print(f"读取文本内容时出错: {e}")
            
            # 检查是否有文件
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                if files != self.last_content:
                    self._handle_new_content('file', '\n'.join(files))
                    self.last_content = files
            
            # 检查是否有图片
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                try:
                    import io
                    from PIL import Image
                    import hashlib
                    import os
                    
                    # 获取图片数据
                    dib_data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                    print(f"获取到图片数据，大小: {len(dib_data)} 字节")
                    
                    # 计算图片数据的哈希值，用于检测变化
                    image_hash = hashlib.md5(dib_data).hexdigest()
                    print(f"图片哈希值: {image_hash}")
                    
                    # 只有当哈希值变化时才处理
                    if image_hash != self.last_content:
                        # 转换为PIL Image
                        image = Image.open(io.BytesIO(dib_data))
                        print(f"图片尺寸: {image.size}")
                        
                        # 保存为临时文件路径（使用绝对路径）
                        temp_path = os.path.join(self.temp_dir, f"temp_image_{image_hash[:8]}.png")
                        print(f"保存图片到: {temp_path}")
                        
                        # 确保目录存在
                        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                        
                        # 保存图片
                        image.save(temp_path)
                        print(f"图片已保存: {temp_path}")
                        
                        # 检查文件是否真的存在
                        if os.path.exists(temp_path):
                            print(f"图片文件确认存在: {temp_path}")
                        else:
                            print(f"警告: 图片文件不存在: {temp_path}")
                        
                        self._handle_new_content('image', temp_path)
                        self.last_content = image_hash
                    else:
                        print("图片内容未变化，跳过处理")
                except Exception as e:
                    print(f"处理图片时出错: {e}")
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            print(f"读取剪贴板时出错: {e}")
        finally:
            try:
                win32clipboard.CloseClipboard()
                print("成功关闭剪贴板")
            except Exception as e:
                print(f"关闭剪贴板时出错: {e}")
    
    def _handle_new_content(self, content_type, content):
        """处理新内容
        
        Args:
            content_type: 内容类型 (text/file/image)
            content: 内容
        """
        print(f"开始处理新内容，类型: {content_type}")
        # 创建记录
        record = {
            'id': datetime.now().timestamp(),
            'content': content,
            'type': content_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'favorited': False
        }
        
        # 保存到存储
        print(f"正在保存记录到存储")
        self.storage.add_record(record)
        
        # 通知存储变更
        if hasattr(self.storage, 'notify_change'):
            print("正在通知存储变更")
            self.storage.notify_change()
        print("新内容处理完成")