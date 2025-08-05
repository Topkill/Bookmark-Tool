# 文件名: 批量书签去重.py
# (原文件名: run_batch.py)

import os
import glob
import argparse
import subprocess
import sys

def run_for_all_files(args):
    """
    查找指定目录下的所有HTML文件，并使用外部脚本对每个文件以用户指定的模式运行去重。
    """
    directory = args.directory
    script_to_run = args.script
    modes_to_run = args.modes_to_run

    search_path = os.path.join(directory, '*.html')
    html_files = glob.glob(search_path)

    if not html_files:
        print(f"错误: 在目录 '{directory}' 中未找到任何 .html 文件。")
        return

    print(f"发现 {len(html_files)} 个HTML文件。即将开始批量处理...")
    print(f"将要调用的去重脚本: {script_to_run}")
    print(f"将要执行的去重模式: {', '.join(modes_to_run)}")
    
    # 打印将要传递的通用参数
    print("\n--- 通用处理参数 ---")
    print(f"URL 解码 (-d): {'启用' if args.decode else '禁用'}")
    print(f"严格协议区分 (--strict-protocol): {'启用' if args.strict_protocol else '禁用'}")
    print(f"忽略末尾斜杠 (--ignore-slash): {'启用' if args.ignore_slash else '禁用'}")
    print("="*70)

    # 遍历找到的每个文件
    for i, filepath in enumerate(html_files):
        print(f"\n--- 文件 {i+1}/{len(html_files)}: {os.path.basename(filepath)} ---\n")
        
        # 根据用户选择的模式列表进行循环
        for j, mode in enumerate(modes_to_run):
            print(f"--- 模式 {j+1}/{len(modes_to_run)}: '{mode}' ---")
            
            # --- 核心改动：构建并执行外部命令 ---
            command = [sys.executable, script_to_run, filepath, '-m', mode]
            
            # 根据用户选择，动态添加可选参数
            if args.decode:
                command.append('-d')
            if args.strict_protocol:
                command.append('--strict-protocol')
            if args.ignore_slash:
                command.append('--ignore-slash')
            
            try:
                # 打印将要执行的完整命令，非常清晰
                print(f"--> 执行命令: {' '.join(command)}")
                
                # 使用 subprocess 运行外部脚本，并捕获输出
                result = subprocess.run(
                    command, 
                    check=True,        # 如果子进程返回非零退出码，则引发异常
                    capture_output=True, # 捕获 stdout 和 stderr
                    text=True,           # 将 stdout 和 stderr 解码为文本
                    encoding='utf-8'     # 指定编码以避免乱码
                )
                
                # 打印子进程的输出
                print(result.stdout)

            except FileNotFoundError:
                print(f"!!! 严重错误: 无法找到Python解释器 '{sys.executable}' 或脚本 '{script_to_run}'。请检查路径。")
                return # 中止执行
            except subprocess.CalledProcessError as e:
                # 如果子进程出错，打印详细信息
                print(f"!!! 在处理 '{os.path.basename(filepath)}' ({mode}模式) 时发生错误。")
                print("--- 子进程输出 (stdout): ---")
                print(e.stdout)
                print("--- 子进程错误 (stderr): ---")
                print(e.stderr)
                print("-" * 30)
            except Exception as e:
                print(f"!!! 发生未知严重错误: {e}")
            
            # 如果一个文件有多种模式要跑，在模式之间打印分隔符
            if j < len(modes_to_run) - 1:
                print("\n" + "-"*50 + "\n")

        print("="*70)

    print("\n所有文件的批量处理已全部完成！")

def main():
    parser = argparse.ArgumentParser(
        description="批量调用一个指定的书签去重脚本，处理文件夹下的所有HTML文件。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # --- 新增和修改的参数 ---
    parser.add_argument("script", help="要调用的去重脚本的路径 (例如: deduplicate_bookmarks-健壮版1.py)")
    parser.add_argument("directory", help="包含HTML书签文件的文件夹路径。")
    
    # --- 用于控制批处理本身的参数 ---
    parser.add_argument(
        "-bm", "--batch-mode",
        choices=['url', 'url-title', 'all'],
        default='all',
        dest='mode', # 保持与旧版args.mode的兼容性
        help="选择对每个文件执行的去重模式 (默认为: all)。\n"
             "  url:       只运行'按URL去重'模式。\n"
             "  url-title: 只运行'按URL和标题去重'的严格模式。\n"
             "  all:       对每个文件依次运行以上两种模式。"
    )
    
    # --- 用于传递给目标脚本的参数 ---
    parser.add_argument(
        "-d", "--decode",
        action='store_true',
        help="【传递参数】启用URL解码。将会把 '-d' 传递给目标脚本。"
    )
    parser.add_argument(
        '--strict-protocol',
        action='store_true',
        help="【传递参数】严格区分 http 和 https。将会把 '--strict-protocol' 传递给目标脚本。"
    )
    parser.add_argument(
        '--ignore-slash',
        action='store_true',
        help="【传递参数】忽略URL末尾的斜杠'/'。将会把 '--ignore-slash' 传递给目标脚本。"
    )
    
    args = parser.parse_args()
    
    # --- 验证输入 ---
    if not os.path.isfile(args.script):
        print(f"错误: 提供的脚本路径 '{args.script}' 不存在或不是一个文件。")
        return
    if not os.path.isdir(args.directory):
        print(f"错误: 提供的目录路径 '{args.directory}' 不存在或不是一个目录。")
        return
    
    # 根据用户的选择，决定要运行的模式列表
    if args.mode == 'all':
        args.modes_to_run = ['url', 'url-title']
    else:
        args.modes_to_run = [args.mode]
        
    run_for_all_files(args)

if __name__ == '__main__':
    main()
