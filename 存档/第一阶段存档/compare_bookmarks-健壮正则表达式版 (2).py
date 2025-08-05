# -*- coding: utf-8 -*-
"""
【健壮正则版】
比较两个HTML书签文件，找出它们之间的差异并生成报告。
- 使用正则表达式，无需第三方库。
- 始终进行HTML实体解码(& -> &)，确保结果准确。
- URL百分号编码解码(%%XX -> char)功能变为可选。
"""
import argparse
import time
from datetime import datetime
import os
from urllib.parse import unquote
import re
import html

def parse_bookmarks_file(filepath, mode, filter_enabled, decode_enabled):
    """
    【健壮正则版】使用正则表达式解析文件。
    - 始终进行HTML实体解码。
    - URL百分号编码解码由 decode_enabled 开关控制。
    """
    print(f"正在以 '{mode}' 模式健壮正则解析文件: {filepath} (过滤: {'启用' if filter_enabled else '禁用'}, 百分号解码: {'启用' if decode_enabled else '禁用'}) ...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{filepath}' 未找到。")
        return None, 0, None, 0
    except Exception as e:
        print(f"读取或解析文件 '{filepath}' 时出错: {e}")
        return None, 0, None, 0

    # --- 文件夹统计 ---
    folder_pattern = re.compile(r'<h3[^>]*>(.*?)</h3>', re.IGNORECASE | re.DOTALL)
    raw_folders = folder_pattern.findall(content)
    total_folders_count = len(raw_folders)
    folders_set = {re.sub(r'<.*?>', '', html.unescape(f), flags=re.DOTALL).strip() for f in raw_folders}

    # --- 书签统计 ---
    bookmark_pattern = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
    raw_bookmarks = bookmark_pattern.findall(content)
    
    all_valid_bookmarks = []
    for raw_url, raw_title in raw_bookmarks:
        if raw_url:
            # 1. 始终进行HTML实体解码
            unescaped_url = html.unescape(raw_url)
            unescaped_title = html.unescape(raw_title)

            # 2. 【核心改动】根据开关决定是否进行百分号解码
            normalized_url = unescaped_url
            if decode_enabled:
                normalized_url = unquote(unescaped_url)

            should_add = True
            if filter_enabled:
                if not normalized_url.lower().startswith(('http', 'https', 'ftp')):
                    should_add = False
            
            if should_add:
                if mode == 'url':
                    all_valid_bookmarks.append(normalized_url)
                elif mode == 'url-title':
                    clean_title = re.sub(r'<.*?>', '', unescaped_title, flags=re.DOTALL).strip()
                    all_valid_bookmarks.append((normalized_url, clean_title))
    
    total_bookmarks_count = len(all_valid_bookmarks)
    bookmarks_set = set(all_valid_bookmarks)

    print(f"解析完成: 找到 {total_bookmarks_count} 个书签 ({len(bookmarks_set)}个唯一), "
          f"{total_folders_count} 个文件夹 ({len(folders_set)}个唯一)。")
    
    return bookmarks_set, total_bookmarks_count, folders_set, total_folders_count

def generate_report(file1, file2, output_file, mode, filter_enabled, decode_enabled):
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
    report_lines.append("          书签文件差异分析报告 (健壮正则版)")
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
    report_lines.append(f"协议过滤: {'已启用' if filter_enabled else '已禁用'}")
    report_lines.append(f"URL解码: {'已启用' if decode_enabled else '已禁用'}")
    report_lines.append("-" * 60)
    
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
    parser = argparse.ArgumentParser(description="【健壮正则版】比较两个HTML书签文件，找出它们之间的差异并生成报告。", formatter_class=argparse.RawTextHelpFormatter)
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
        help="【可选】启用协议过滤，只统计 http, https, ftp 协议的书签。"
    )

    parser.add_argument(
        "-d", "--decode",
        action='store_true',
        help="【可选】启用URL百分号解码(例如: %%20 -> 空格)。\n"
             "         (HTML实体如 & 会被始终解码)。"
    )
    
    args = parser.parse_args()

    base1 = os.path.splitext(os.path.basename(args.file1))[0]
    base2 = os.path.splitext(os.path.basename(args.file2))[0]
    
    output_file = f"【差异报告】{base1}_VS_{base2}_{args.mode}模式.txt"
    
    generate_report(args.file1, args.file2, output_file, args.mode, args.filter, args.decode)

if __name__ == '__main__':
    main()
