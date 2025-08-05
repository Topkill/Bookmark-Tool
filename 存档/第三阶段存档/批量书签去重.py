import os
import glob
import argparse
import subprocess
import sys
import collections

def run_for_all_files(args):
    """
    处理用户提供的所有路径（文件或目录），并使用外部脚本对每个找到的HTML文件运行去重。
    该版本能识别并报告被重复指定的文件路径，并总是列出最终处理列表。
    """
    targets = args.targets
    script_to_run = args.script
    modes_to_run = args.modes_to_run

    all_discovered_paths = []
    
    print("正在分析提供的路径...")
    for target_path in targets:
        abs_target_path = os.path.abspath(target_path)

        if os.path.isdir(abs_target_path):
            search_path = os.path.join(abs_target_path, '*.html')
            found_files = glob.glob(search_path)
            if found_files:
                print(f"在目录 '{target_path}' 中找到 {len(found_files)} 个 .html 文件。")
                all_discovered_paths.extend(found_files)
            else:
                print(f"注意: 在目录 '{target_path}' 中未找到任何 .html 文件。")
        elif os.path.isfile(abs_target_path):
            if abs_target_path.lower().endswith('.html'):
                all_discovered_paths.append(abs_target_path)
            else:
                print(f"警告: 文件 '{target_path}' 不是一个 .html 文件，将跳过。")
        else:
            print(f"警告: 路径 '{target_path}' 不存在或不是有效的文件/目录，将跳过。")

    path_counts = collections.Counter(all_discovered_paths)
    html_files = sorted(list(path_counts.keys()))

    duplicates_info = {path: count for path, count in path_counts.items() if count > 1}
    if duplicates_info:
        print("\n" + "="*25 + " 重复路径警告 " + "="*25)
        print("以下文件路径被指定了多次 (例如，同时指定了目录和其中的文件):")
        for path, count in duplicates_info.items():
            print(f"  - 文件: {path}")
            print(f"    (被指定 {count} 次)")
        print("\n为避免重复工作，每个文件将只会被处理一次。")
        print("="*66)

    if not html_files:
        print(f"\n错误: 未能从提供的路径中找到任何有效的 .html 文件。")
        return

    # 无论有无重复，都打印最终处理列表
    print(f"\n--- 将处理以下 {len(html_files)} 个独立文件 ---")
    for i, path in enumerate(html_files, 1):
        print(f"  {i}. {path}")
    print("------------------------------------------")

    print(f"\n将要调用的去重脚本: {script_to_run}")
    print(f"将要执行的去重模式: {', '.join(modes_to_run)}")
    
    print("\n--- 通用处理参数 ---")
    print(f"URL 解码 (-d): {'启用' if args.decode else '禁用'}")
    print(f"严格协议区分 (--strict-protocol): {'启用' if args.strict_protocol else '禁用'}")
    print(f"忽略末尾斜杠 (--ignore-slash): {'启用' if args.ignore_slash else '禁用'}")
    print("="*70)

    for i, filepath in enumerate(html_files):
        print(f"\n--- 文件 {i+1}/{len(html_files)}: {os.path.basename(filepath)} (路径: {filepath}) ---\n")
        
        for j, mode in enumerate(modes_to_run):
            print(f"--- 模式 {j+1}/{len(modes_to_run)}: '{mode}' ---")
            
            command = [sys.executable, script_to_run, filepath, '-m', mode]
            
            if args.decode:
                command.append('-d')
            if args.strict_protocol:
                command.append('--strict-protocol')
            if args.ignore_slash:
                command.append('--ignore-slash')
            
            try:
                print(f"--> 执行命令: {' '.join(command)}")
                
                result = subprocess.run(
                    command, 
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                print(result.stdout)

            except FileNotFoundError:
                print(f"!!! 严重错误: 无法找到Python解释器 '{sys.executable}' 或脚本 '{script_to_run}'。请检查路径。")
                return
            except subprocess.CalledProcessError as e:
                print(f"!!! 在处理 '{os.path.basename(filepath)}' ({mode}模式) 时发生错误。")
                print("--- 子进程输出 (stdout): ---")
                print(e.stdout)
                print("--- 子进程错误 (stderr): ---")
                print(e.stderr)
                print("-" * 30)
            except Exception as e:
                print(f"!!! 发生未知严重错误: {e}")
            
            if j < len(modes_to_run) - 1:
                print("\n" + "-"*50 + "\n")

        print("="*70)

    print("\n所有文件的批量处理已全部完成！")

def main():
    parser = argparse.ArgumentParser(
        description="批量调用一个指定的书签去重脚本，处理文件夹和/或文件。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("script", help="要调用的去重脚本的路径 (例如: deduplicate_bookmarks-健壮版1.py)")
    parser.add_argument(
        "targets", 
        nargs='+',
        help="一个或多个要处理的路径。可以是目录，也可以是具体的 .html 文件。"
    )
    
    parser.add_argument(
        "-bm", "--batch-mode",
        choices=['url', 'url-title', 'all'],
        default='all',
        dest='mode',
        help="选择对每个文件执行的去重模式 (默认为: all)。\n"
             "  url:       只运行'按URL去重'模式。\n"
             "  url-title: 只运行'按URL和标题去重'的严格模式。\n"
             "  all:       对每个文件依次运行以上两种模式。"
    )
    
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
    
    if not os.path.isfile(args.script):
        print(f"错误: 提供的脚本路径 '{args.script}' 不存在或不是一个文件。")
        return
    
    if args.mode == 'all':
        args.modes_to_run = ['url', 'url-title']
    else:
        args.modes_to_run = [args.mode]
        
    run_for_all_files(args)

if __name__ == '__main__':
    main()
