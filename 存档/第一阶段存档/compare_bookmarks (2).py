import argparse
import time
from datetime import datetime
from bs4 import BeautifulSoup
import os
from urllib.parse import unquote

def parse_bookmarks_file(filepath, mode, filter_enabled, decode_enabled):
    """
    【最终版】使用 BeautifulSoup 解析文件。
    - URL解码功能由 decode_enabled 开关控制。
    """
    print(f"正在以 '{mode}' 模式解析文件: {filepath} (过滤: {'启用' if filter_enabled else '禁用'}, 解码: {'启用' if decode_enabled else '禁用'}) ...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
    except FileNotFoundError:
        print(f"错误: 文件 '{filepath}' 未找到。")
        return None, 0, None, 0
    except Exception as e:
        print(f"读取或解析文件 '{filepath}' 时出错: {e}")
        return None, 0, None, 0

    # --- 文件夹统计 ---
    all_h3_tags = soup.find_all('h3')
    total_folders_count = len(all_h3_tags)
    folders_set = {h3.get_text().strip() for h3 in all_h3_tags}

    # --- 书签统计 ---
    all_a_tags = soup.find_all('a')
    all_valid_bookmarks = []
    for a_tag in all_a_tags:
        url = a_tag.get('href')
        
        if url:
            normalized_url = url
            # 【核心改动】根据开关决定是否解码
            if decode_enabled:
                normalized_url = unquote(url)

            should_add = True
            if filter_enabled:
                if not normalized_url.lower().startswith(('http', 'https', 'ftp')):
                    should_add = False

            if should_add:
                if mode == 'url':
                    all_valid_bookmarks.append(normalized_url)
                elif mode == 'url-title':
                    title = a_tag.get_text().strip()
                    all_valid_bookmarks.append((normalized_url, title))
    
    total_bookmarks_count = len(all_valid_bookmarks)
    bookmarks_set = set(all_valid_bookmarks)

    print(f"解析完成: 找到 {total_bookmarks_count} 个书签 ({len(bookmarks_set)}个唯一), "
          f"{total_folders_count} 个文件夹 ({len(folders_set)}个唯一)。")
    
    return bookmarks_set, total_bookmarks_count, folders_set, total_folders_count

def generate_report(file1, file2, output_file, mode, filter_enabled, decode_enabled):
    """
    【最终版】报告生成函数。
    """
    start_time = time.time()
    
    bookmarks1_set, total_bookmarks1, folders1_set, total_folders1 = parse_bookmarks_file(file1, mode, filter_enabled, decode_enabled)
    if bookmarks1_set is None: return

    bookmarks2_set, total_bookmarks2, folders2_set, total_folders2 = parse_bookmarks_file(file2, mode, filter_enabled, decode_enabled)
    if bookmarks2_set is None: return

    print("\n正在进行差异比较...")
    
    bookmarks_only_in_1 = bookmarks1_set - bookmarks2_set
    bookmarks_only_in_2 = bookmarks2_set - bookmarks1_set
    folders_only_in_1 = folders1_set - folders2_set
    folders_only_in_2 = folders2_set - folders1_set

    print("比较完成，正在生成报告...")
    
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("          书签文件差异分析报告")
    report_lines.append("=" * 60)
    report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("-" * 60)
    
    report_lines.append(f"文件 A: {os.path.basename(file1)}")
    report_lines.append(f"  - 总书签数: {total_bookmarks1} (唯一: {len(bookmarks1_set)})")
    report_lines.append(f"  - 总文件夹数: {total_folders1} (唯一: {len(folders1_set)})")
    
    report_lines.append(f"文件 B: {os.path.basename(file2)}")
    report_lines.append(f"  - 总书签数: {total_bookmarks2} (唯一: {len(bookmarks2_set)})")
    report_lines.append(f"  - 总文件夹数: {total_folders2} (唯一: {len(folders2_set)})")
    
    report_lines.append(f"比较模式: {mode}")
    report_lines.append(f"协议过滤: {'已启用 (只保留http,https,ftp)' if filter_enabled else '已禁用 (保留所有链接)'}")
    report_lines.append(f"URL 解码: {'已启用' if decode_enabled else '已禁用 (使用原始URL)'}")
    report_lines.append("-" * 60)
    
    # ... (其余报告逻辑不变) ...
    report_lines.append(f"\n【文件夹差异】\n")
    report_lines.append(f"--- 在 '{os.path.basename(file1)}' 中存在，但在 '{os.path.basename(file2)}' 中缺失的文件夹 ({len(folders_only_in_1)}个) ---")
    if folders_only_in_1:
        for folder in sorted(list(folders_only_in_1)): report_lines.append(f"  - {folder}")
    else: report_lines.append("  (无)")
    report_lines.append(f"\n--- 在 '{os.path.basename(file2)}' 中存在，但在 '{os.path.basename(file1)}' 中缺失的文件夹 ({len(folders_only_in_2)}个) ---")
    if folders_only_in_2:
        for folder in sorted(list(folders_only_in_2)): report_lines.append(f"  - {folder}")
    else: report_lines.append("  (无)")
    report_lines.append("\n" + "=" * 60)
    report_lines.append(f"\n【书签差异】\n")
    report_lines.append(f"--- 在 '{os.path.basename(file1)}' 中存在，但在 '{os.path.basename(file2)}' 中缺失的书签 ({len(bookmarks_only_in_1)}个) ---")
    if bookmarks_only_in_1:
        for item in sorted(list(bookmarks_only_in_1)):
            if mode == 'url-title':
                url, title = item
                report_lines.append(f"  - [ {title} ] {url}")
            else:
                report_lines.append(f"  - {item}")
    else: report_lines.append("  (无)")
    report_lines.append(f"\n--- 在 '{os.path.basename(file2)}' 中存在，但在 '{os.path.basename(file1)}' 中缺失的书签 ({len(bookmarks_only_in_2)}个) ---")
    if bookmarks_only_in_2:
        for item in sorted(list(bookmarks_only_in_2)):
            if mode == 'url-title':
                url, title = item
                report_lines.append(f"  - [ {title} ] {url}")
            else:
                report_lines.append(f"  - {item}")
    else: report_lines.append("  (无)")
    report_lines.append("\n" + "=" * 60)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f: f.write('\n'.join(report_lines))
        total_time = time.time() - start_time
        print(f"\n报告 '{output_file}' 已成功生成！总耗时: {total_time:.2f} 秒。")
    except Exception as e: print(f"写入报告文件时出错: {e}")

def main():
    """主函数，处理命令行参数。"""
    parser = argparse.ArgumentParser(description="【最终版】比较两个HTML书签文件，找出它们之间的差异并生成报告。", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("file1", help="第一个书签文件 (文件A) 的路径。")
    parser.add_argument("file2", help="第二个书签文件 (文件B) 的路径。")
    parser.add_argument(
        "-m", "--mode",
        choices=['url', 'url-title'],
        default='url',
        help="选择书签的比较模式 (默认为: url)。\n"
             "  url:       只比较链接地址(URL)。\n"
             "  url-title: 严格比较链接地址(URL)和标题。",
    )
    parser.add_argument(
        "-f", "--filter",
        action='store_true',
        help="【可选】启用协议过滤，只统计 http, https, ftp 协议的书签。\n"
             "         (默认不启用，即统计所有链接)。"
    )

    # 【新增】解码开关
    parser.add_argument(
        "-d", "--decode",
        action='store_true',
        help="【可选】启用URL解码，处理 %%编码 和 & 等HTML实体。\n"
             "         (默认不启用，直接使用原始URL进行比较)。"
    )
    
    args = parser.parse_args()

    base1 = os.path.splitext(os.path.basename(args.file1))[0]
    base2 = os.path.splitext(os.path.basename(args.file2))[0]
    
    output_file = f"【差异报告】{base1}_VS_{base2}_{args.mode}模式.txt"
    
    generate_report(args.file1, args.file2, output_file, args.mode, args.filter, args.decode)

if __name__ == '__main__':
    main()