# -*- coding: utf-8 -*-
import argparse
import time
from datetime import datetime
import os
import re
from urllib.parse import unquote
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
    # 始终进行HTML实体解码
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


# --- 【核心修正区域】analyze_multiple_files 函数 ---
def analyze_multiple_files(files, compare_mode, analysis_mode, filter_enabled, decode_enabled):
    start_time = time.time()
    
    all_data = {}
    for f in files:
        b_set, b_total, f_set, f_total = parse_bookmarks_file(f, compare_mode, filter_enabled, decode_enabled)
        if b_set is None:
            print(f"警告: 文件 {f} 解析失败，将在此次分析中跳过。")
            continue
        all_data[f] = {'b_set': b_set, 'b_total': b_total, 'f_set': f_set, 'f_total': f_total}

    if len(all_data) < 2:
        print("错误: 至少需要两个成功解析的文件才能进行分析。")
        return

    print("\n所有文件解析完成，开始进行分析...")

    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("        多书签文件对比分析报告 (健壮正则版)")
    report_lines.append("=" * 60)
    report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"对比模式: {compare_mode}")
    report_lines.append(f"分析模式: {analysis_mode}")
    report_lines.append(f"协议过滤: {'已启用' if filter_enabled else '已禁用'}")
    report_lines.append(f"URL解码: {'已启用' if decode_enabled else '已禁用'}")
    report_lines.append("-" * 60)
    report_lines.append("【输入文件统计】\n")
    for filepath, data in all_data.items():
        report_lines.append(f"文件: {os.path.basename(filepath)}")
        report_lines.append(f"  - 总书签数: {data['b_total']} (唯一: {len(data['b_set'])})")
        report_lines.append(f"  - 总文件夹数: {data['f_total']} (唯一: {len(data['f_set'])})")
    report_lines.append("-" * 60)

    if analysis_mode == 'intersection':
        file_list = list(all_data.keys())
        # --- 【修正】同时初始化书签和文件夹的集合 ---
        common_bookmarks = all_data[file_list[0]]['b_set'].copy()
        common_folders = all_data[file_list[0]]['f_set'].copy()
        
        for i in range(1, len(file_list)):
            # --- 【修正】同时对书签和文件夹求交集 ---
            common_bookmarks.intersection_update(all_data[file_list[i]]['b_set'])
            common_folders.intersection_update(all_data[file_list[i]]['f_set'])
        
        report_lines.append(f"\n【分析结果: 交集】\n")
        report_lines.append(f"--- 在所有 {len(all_data)} 个文件中共同存在的书签 ({len(common_bookmarks)}个) ---")
        if common_bookmarks:
            for item in sorted(list(common_bookmarks)):
                if isinstance(item, tuple): report_lines.append(f"  - [ {item[1]} ] {item[0]}")
                else: report_lines.append(f"  - {item}")
        else:
            report_lines.append("  (无)")

        # --- 【新增】报告共同存在的文件夹 ---
        report_lines.append(f"\n--- 在所有 {len(all_data)} 个文件中共同存在的文件夹 ({len(common_folders)}个) ---")
        if common_folders:
            for folder in sorted(list(common_folders)):
                report_lines.append(f"  - {folder}")
        else:
            report_lines.append("  (无)")

    elif analysis_mode == 'unique':
        report_lines.append(f"\n【分析结果: 独有项】\n")
        all_filepaths = list(all_data.keys())
        for i, filepath in enumerate(all_filepaths):
            other_bookmarks_union = set()
            # --- 【修正】同时为书签和文件夹创建并集 ---
            other_folders_union = set()
            for j, other_filepath in enumerate(all_filepaths):
                if i == j: continue
                other_bookmarks_union.update(all_data[other_filepath]['b_set'])
                other_folders_union.update(all_data[other_filepath]['f_set'])
            
            # --- 【修正】同时计算独有的书签和文件夹 ---
            unique_bookmarks = all_data[filepath]['b_set'] - other_bookmarks_union
            unique_folders = all_data[filepath]['f_set'] - other_folders_union
            
            report_lines.append(f"--- 文件 '{os.path.basename(filepath)}' 的独有项 ---")
            report_lines.append(f"  【独有书签 ({len(unique_bookmarks)}个)】")
            if unique_bookmarks:
                for item in sorted(list(unique_bookmarks)):
                    if isinstance(item, tuple): report_lines.append(f"    - [ {item[1]} ] {item[0]}")
                    else: report_lines.append(f"    - {item}")
            else:
                report_lines.append("    (无)")
            
            # --- 【新增】报告独有的文件夹 ---
            report_lines.append(f"\n  【独有文件夹 ({len(unique_folders)}个)】")
            if unique_folders:
                for folder in sorted(list(unique_folders)):
                    report_lines.append(f"    - {folder}")
            else:
                report_lines.append("    (无)")
            report_lines.append("")

    report_lines.append("\n" + "=" * 60)
    
    filter_tag = "过滤-启用" if filter_enabled else "过滤-禁用"
    decode_tag = "解码-启用" if decode_enabled else "解码-禁用"
    output_file = f"【多文件分析报告】_{analysis_mode}_{compare_mode}模式_{filter_tag}_{decode_tag}.txt"
    try:
        with open(output_file, 'w', encoding='utf-8') as f: f.write('\n'.join(report_lines))
        total_time = time.time() - start_time
        print(f"\n报告 '{output_file}' 已成功生成！总耗时: {total_time:.2f} 秒。")
    except Exception as e: print(f"写入报告文件时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="【健壮正则版】比较多个HTML书签文件，分析它们的交集或独有项。", formatter_class=argparse.RawTextHelpFormatter)
    
    parser.add_argument("files", nargs='+', help="需要对比的一个或多个书签文件路径。")
    
    parser.add_argument(
        "-c", "--compare-mode",
        choices=['url', 'url-title'],
        default='url',
        dest='compare_mode',
        help="选择书签的判断依据 (默认为: url)。\n"
             "  url:       只比较链接地址(URL)。\n"
             "  url-title: 严格比较链接地址(URL)和标题。",
    )

    parser.add_argument(
        "-a", "--analysis",
        choices=['intersection', 'unique'],
        default='unique',
        help="选择分析模式 (默认为: unique)。\n"
             "  intersection: 找出在所有文件中都存在的共同书签。\n"
             "  unique:       找出每个文件中独有的书签。",
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

    if len(args.files) < 2:
        print("错误: 请至少提供两个文件进行对比。")
        return

    analyze_multiple_files(args.files, args.compare_mode, args.analysis, args.filter, args.decode)

if __name__ == '__main__':
    main()