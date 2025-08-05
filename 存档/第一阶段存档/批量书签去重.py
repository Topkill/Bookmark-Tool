# 文件名: run_batch.py

import os
import glob
import argparse
# 从我们自己的工具脚本中，导入核心的处理函数
from deduplicate_bookmarks import deduplicate_and_generate_report

def run_for_all_files(directory, modes_to_run):
    """
    查找指定目录下的所有HTML文件，并对每个文件以用户指定的模式运行去重脚本。
    """
    search_path = os.path.join(directory, '*.html')
    html_files = glob.glob(search_path)

    if not html_files:
        print(f"错误: 在目录 '{directory}' 中未找到任何 .html 文件。")
        return

    print(f"发现 {len(html_files)} 个HTML文件。即将开始批量处理...")
    print(f"将要执行的去重模式: {', '.join(modes_to_run)}")
    print("="*70)

    # 遍历找到的每个文件
    for i, filepath in enumerate(html_files):
        print(f"\n--- 文件 {i+1}/{len(html_files)}: {os.path.basename(filepath)} ---\n")
        
        # 根据用户选择的模式列表进行循环
        for j, mode in enumerate(modes_to_run):
            print(f"--- 模式 {j+1}/{len(modes_to_run)}: '{mode}' 模式 ---")
            try:
                # 调用核心处理函数，传入当前文件和当前模式
                deduplicate_and_generate_report(filepath, mode)
            except Exception as e:
                print(f"!!! 在处理 '{filepath}' ({mode}模式) 时发生严重错误: {e}\n")
            
            # 如果一个文件有多种模式要跑，在模式之间打印分隔符
            if j < len(modes_to_run) - 1:
                print("\n" + "-"*50 + "\n")

        print("="*70)

    print("\n所有文件的批量处理已全部完成！")

def main():
    parser = argparse.ArgumentParser(
        description="批量处理指定文件夹下的所有HTML书签文件，可指定一种或多种去重模式。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("directory", help="包含HTML书签文件的文件夹路径。")
    parser.add_argument(
        "-m", "--mode",
        choices=['url', 'url-title', 'all'],
        default='all',
        help="选择去重模式 (默认为: all)。\n"
             "  url:       只运行'按URL去重'模式。\n"
             "  url-title: 只运行'按URL和标题去重'的严格模式。\n"
             "  all:       对每个文件运行以上两种模式。"
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"错误: 提供的路径 '{args.directory}' 不是一个有效的目录。")
        return
    
    # 根据用户的选择，决定要运行的模式列表
    if args.mode == 'all':
        modes_to_run = ['url', 'url-title']
    else:
        # 如果用户选择 'url' 或 'url-title'，列表里就只有一个元素
        modes_to_run = [args.mode]
        
    run_for_all_files(args.directory, modes_to_run)

if __name__ == '__main__':
    main()