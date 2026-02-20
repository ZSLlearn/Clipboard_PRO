#!/usr/bin/env python3
"""
存储模块 - 负责剪贴板历史的持久化存储
"""

import json
import os
from datetime import datetime


def delete_file_permanently(file_path):
    """彻底删除文件（不进入回收站）
    
    Args:
        file_path: 文件路径
    """
    try:
        # Windows系统：使用Windows API彻底删除文件
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            
            # 定义Windows API常量
            FO_DELETE = 0x0003
            FOF_NOCONFIRMATION = 0x0010
            FOF_NOERRORUI = 0x0400
            FOF_SILENT = 0x0004
            
            # 定义SHFILEOPSTRUCT结构
            class SHFILEOPSTRUCT(ctypes.Structure):
                _fields_ = [
                    ('hwnd', wintypes.HWND),
                    ('wFunc', wintypes.UINT),
                    ('pFrom', wintypes.LPCWSTR),
                    ('pTo', wintypes.LPCWSTR),
                    ('fFlags', wintypes.UINT),  # 使用UINT代替FILEOP_FLAGS
                    ('fAnyOperationsAborted', wintypes.BOOL),
                    ('hNameMappings', wintypes.HANDLE),
                    ('lpszProgressTitle', wintypes.LPCWSTR)
                ]
            
            # 加载shell32.dll
            shell32 = ctypes.windll.shell32
            SHFileOperation = shell32.SHFileOperationW
            SHFileOperation.argtypes = [
                ctypes.POINTER(SHFILEOPSTRUCT),
            ]
            SHFileOperation.restype = wintypes.BOOL
            
            # 准备文件路径（需要双空格结尾）
            from_path = file_path + '\0\0'
            to_path = '\0\0'
            
            # 创建结构体
            file_op = SHFILEOPSTRUCT()
            file_op.wFunc = FO_DELETE
            file_op.pFrom = from_path
            file_op.pTo = to_path
            file_op.fFlags = FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_SILENT
            file_op.hwnd = None
            file_op.hNameMappings = None
            file_op.lpszProgressTitle = None
            
            # 调用Windows API删除文件
            result = SHFileOperation(ctypes.byref(file_op))
            if result:
                print(f"已彻底删除文件: {file_path}")
                return True
            else:
                print(f"删除文件失败: {file_path}")
                return False
        else:
            # 非Windows系统：直接删除
            os.unlink(file_path)
            print(f"已删除文件: {file_path}")
            return True
    except Exception as e:
        print(f"删除文件时出错: {e}")
        return False


class Storage:
    """存储类"""
    
    def __init__(self, config=None, max_records=50):
        """初始化
        
        Args:
            config: 配置实例
            max_records: 最大存储条数（已废弃，使用config）
        """
        self.config = config
        self.max_records = max_records if config is None else config.get_max_records()
        # 存储到程序目录
        self.data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clipboard_data.json')
        self.records = []
        self.observers = []
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
                # 确保按时间戳倒序
                self.records.sort(key=lambda x: x['id'], reverse=True)
                # 根据存留时间过滤过期记录
                self._filter_by_age()
                # 限制数量（仅在设置了最大记录数时）
                if self.max_records is not None:
                    self.records = self.records[:self.max_records]
                # 清理孤立的图片文件
                self._cleanup_orphaned_images()
        except Exception as e:
            print(f"加载数据时出错: {e}")
            self.records = []
    
    def _cleanup_orphaned_images(self):
        """清理孤立的图片文件（不在记录中的图片）"""
        try:
            temp_dir = os.path.join(os.path.dirname(self.data_file), 'temp_images')
            if not os.path.exists(temp_dir):
                return
            
            # 获取所有记录中的图片路径
            image_paths_in_records = set()
            for record in self.records:
                if record['type'] == 'image':
                    image_paths_in_records.add(record['content'])
            
            # 遍历 temp_images 目录，删除不在记录中的图片
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path) and file_path not in image_paths_in_records:
                    try:
                        delete_file_permanently(file_path)
                        print(f"已清理孤立图片文件: {file_path}")
                    except Exception as e:
                        print(f"清理孤立图片文件时出错: {e}")
        except Exception as e:
            print(f"清理孤立图片文件时出错: {e}")
    
    def _filter_by_age(self):
        """根据存留时间过滤过期记录"""
        if self.config is None:
            return
        
        max_age_minutes = self.config.get_max_age_minutes()
        if max_age_minutes is None:
            return
        
        import time
        current_time = time.time()
        max_age_seconds = max_age_minutes * 60
        
        # 过滤掉超过存留时间的记录
        filtered_records = []
        records_to_delete = []
        
        for record in self.records:
            record_time = record['id']
            age_seconds = current_time - record_time
            if age_seconds <= max_age_seconds:
                filtered_records.append(record)
            else:
                records_to_delete.append(record)
        
        # 删除过期记录对应的图片文件
        for record in records_to_delete:
            if record['type'] == 'image':
                try:
                    image_path = record['content']
                    if os.path.exists(image_path):
                        delete_file_permanently(image_path)
                        print(f"已删除过期图片文件: {image_path}")
                except Exception as e:
                    print(f"删除过期图片文件时出错: {e}")
        
        self.records = filtered_records
    
    def _save_data(self):
        """保存数据"""
        try:
            # 限制数量，并删除超出限制的图片文件（仅在设置了最大记录数时）
            if self.max_records is not None and len(self.records) > self.max_records:
                records_to_delete = self.records[self.max_records:]
                for record in records_to_delete:
                    if record['type'] == 'image':
                        try:
                            image_path = record['content']
                            if os.path.exists(image_path):
                                delete_file_permanently(image_path)
                                print(f"已删除超出限制的图片文件: {image_path}")
                        except Exception as e:
                            print(f"删除超出限制的图片文件时出错: {e}")
                
                self.records = self.records[:self.max_records]
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据时出错: {e}")
    
    def add_record(self, record):
        """添加记录
        
        Args:
            record: 记录字典
        """
        print(f"正在添加记录: {record['content'][:50]}..." if len(record['content']) > 50 else f"正在添加记录: {record['content']}")
        # 检查是否重复
        for existing_record in self.records:
            if existing_record['content'] == record['content'] and existing_record['type'] == record['type']:
                # 更新时间戳
                existing_record['id'] = record['id']
                existing_record['timestamp'] = record['timestamp']
                # 移到最前面
                self.records.remove(existing_record)
                self.records.insert(0, existing_record)
                self._save_data()
                print("更新了现有记录")
                return
        
        # 添加新记录
        self.records.insert(0, record)
        # 根据存留时间过滤过期记录
        self._filter_by_age()
        # 限制数量（仅在设置了最大记录数时）
        if self.max_records is not None:
            self.records = self.records[:self.max_records]
        # 保存
        self._save_data()
        print(f"添加了新记录，当前记录数: {len(self.records)}")
    
    def update_config(self, config):
        """更新配置
        
        Args:
            config: 新的配置实例
        """
        self.config = config
        self.max_records = config.get_max_records()
        
        # 获取更新前的记录数
        old_count = len(self.records)
        
        # 根据新配置过滤记录
        self._filter_by_age()
        
        # 删除超出最大记录数的记录及其图片文件（仅在设置了最大记录数时）
        if self.max_records is not None and len(self.records) > self.max_records:
            records_to_delete = self.records[self.max_records:]
            for record in records_to_delete:
                if record['type'] == 'image':
                    try:
                        image_path = record['content']
                        if os.path.exists(image_path):
                            delete_file_permanently(image_path)
                            print(f"已删除超出限制的图片文件: {image_path}")
                    except Exception as e:
                        print(f"删除超出限制的图片文件时出错: {e}")
            
            self.records = self.records[:self.max_records]
        
        # 如果记录数减少了，需要保存
        if len(self.records) < old_count:
            self._save_data()
    
    def get_records(self, filter_type=None):
        """获取记录
        
        Args:
            filter_type: 过滤类型 (text/file/image)
            
        Returns:
            记录列表
        """
        result = self.records
        
        # 过滤类型
        if filter_type:
            result = [r for r in result if r['type'] == filter_type]
        
        return result
    
    def delete_record(self, record_id):
        """删除记录
        
        Args:
            record_id: 记录ID
        """
        # 先找到要删除的记录
        record_to_delete = None
        for record in self.records:
            if record['id'] == record_id:
                record_to_delete = record
                break
        
        # 如果是图片类型，删除对应的图片文件
        if record_to_delete and record_to_delete['type'] == 'image':
            try:
                image_path = record_to_delete['content']
                if os.path.exists(image_path):
                    delete_file_permanently(image_path)
            except Exception as e:
                print(f"删除图片文件时出错: {e}")
        
        # 删除记录
        self.records = [r for r in self.records if r['id'] != record_id]
        self._save_data()
    
    def delete_multiple(self, record_ids):
        """批量删除记录
        
        Args:
            record_ids: 记录ID列表
        """
        # 找到要删除的记录
        records_to_delete = []
        for record in self.records:
            if record['id'] in record_ids:
                records_to_delete.append(record)
        
        # 删除对应的图片文件
        for record in records_to_delete:
            if record['type'] == 'image':
                try:
                    image_path = record['content']
                    if os.path.exists(image_path):
                        delete_file_permanently(image_path)
                except Exception as e:
                    print(f"删除图片文件时出错: {e}")
        
        # 删除记录
        self.records = [r for r in self.records if r['id'] not in record_ids]
        self._save_data()
    
    def clear_all(self):
        """清空所有记录"""
        # 删除所有图片文件
        for record in self.records:
            if record['type'] == 'image':
                try:
                    image_path = record['content']
                    if os.path.exists(image_path):
                        delete_file_permanently(image_path)
                except Exception as e:
                    print(f"删除图片文件时出错: {e}")
        
        # 清空记录
        self.records = []
        self._save_data()
        
        # 删除JSON数据文件
        try:
            if os.path.exists(self.data_file):
                delete_file_permanently(self.data_file)
        except Exception as e:
            print(f"删除数据文件时出错: {e}")
        
        # 删除临时图片目录
        try:
            temp_dir = os.path.join(os.path.dirname(self.data_file), 'temp_images')
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                print(f"已删除临时目录: {temp_dir}")
        except Exception as e:
            print(f"删除临时目录时出错: {e}")
    
    def add_observer(self, observer):
        """添加观察者
        
        Args:
            observer: 观察者对象，需要有update方法
        """
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer):
        """移除观察者
        
        Args:
            observer: 观察者对象
        """
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify_change(self):
        """通知所有观察者"""
        for observer in self.observers:
            try:
                # 优先调用on_storage_change方法
                if hasattr(observer, 'on_storage_change'):
                    observer.on_storage_change()
                # 兼容旧的update方法
                elif hasattr(observer, 'update'):
                    observer.update()
            except Exception as e:
                print(f"通知观察者时出错: {e}")
