#!/usr/bin/env python3
"""
打包脚本 - 将项目打包成独立的exe文件
"""

import os
import sys
import subprocess
import shutil


def check_dependencies():
    """检查依赖是否安装"""
    print("检查依赖...")
    
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装 (版本: {PyInstaller.__version__})")
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("✓ PyInstaller 安装完成")
    
    print("检查项目依赖...")
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        for req in requirements:
            try:
                __import__(req.split('==')[0].split('>=')[0].split('<=')[0].replace('-', '_'))
                print(f"✓ {req}")
            except ImportError:
                print(f"✗ {req} 未安装")
                print(f"正在安装 {req}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])
                print(f"✓ {req} 安装完成")
    except Exception as e:
        print(f"检查依赖时出错: {e}")


def clean_build_dirs():
    """清理构建目录"""
    print("\n清理构建目录...")
    
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✓ 已删除 {dir_name}")
            except Exception as e:
                print(f"✗ 删除 {dir_name} 失败: {e}")
    
    # 清理spec文件（如果存在）
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec') and f != 'ClipboardPRO.spec']
    for spec_file in spec_files:
        try:
            os.remove(spec_file)
            print(f"✓ 已删除 {spec_file}")
        except Exception as e:
            print(f"✗ 删除 {spec_file} 失败: {e}")


def build_exe():
    """构建exe文件"""
    print("\n开始构建exe文件...")
    
    # 使用spec文件构建
    if os.path.exists('ClipboardPRO.spec'):
        print("使用 ClipboardPRO.spec 配置文件...")
        cmd = [sys.executable, '-m', 'PyInstaller', 'ClipboardPRO.spec', '--clean']
    else:
        print("使用默认配置...")
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            'main.py',
            '--name=ClipboardPRO',
            '--onefile',
            '--windowed',
            '--icon=icon.ico',
            '--add-data=icon.ico;.',
            '--hidden-import=PyQt6',
            '--hidden-import=pywin32',
            '--hidden-import=pyperclip',
            '--hidden-import=PIL',
            '--clean'
        ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n✓ 构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 构建失败: {e}")
        return False


def check_output():
    """检查输出文件"""
    print("\n检查输出文件...")
    
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        exe_files = [f for f in os.listdir(dist_dir) if f.endswith('.exe')]
        if exe_files:
            for exe_file in exe_files:
                exe_path = os.path.join(dist_dir, exe_file)
                file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
                print(f"✓ {exe_file} ({file_size:.2f} MB)")
                print(f"  路径: {os.path.abspath(exe_path)}")
            return True
        else:
            print("✗ 未找到exe文件")
            return False
    else:
        print("✗ dist 目录不存在")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("剪贴板管理软件 - 打包脚本")
    print("=" * 60)
    
    # 检查依赖
    check_dependencies()
    
    # 清理构建目录
    clean_build_dirs()
    
    # 构建exe
    if build_exe():
        # 检查输出
        if check_output():
            print("\n" + "=" * 60)
            print("打包完成！")
            print("=" * 60)
            print("\n使用说明：")
            print("1. exe文件位于 dist 目录中")
            print("2. 可以直接双击运行，无需安装Python")
            print("3. 可以将exe文件发送给其他人使用")
            print("\n注意事项：")
            print("1. 首次运行可能需要防火墙/杀毒软件允许")
            print("2. 需要Windows 10或更高版本")
            print("3. 建议在Windows 11上运行以获得最佳体验")
        else:
            print("\n✗ 打包失败，请检查错误信息")
            sys.exit(1)
    else:
        print("\n✗ 打包失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
