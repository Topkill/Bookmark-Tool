# -*- coding: utf-8 -*-
import argparse
import time
from datetime import datetime
import os
from urllib.parse import unquote
from html.parser import HTMLParser
from urllib.parse import unquote

class BookmarkParser(HTMLParser):
    """
    一个基于事件驱动的高性能书签解析器。
    """
    def __init__(self, mode, filter_enabled, decode_enabled):
        super().__init__()
        # 传入配置
        self.mode = mode
        self.filter_enabled = filter_enabled
        self.decode_enabled = decode_enabled
        
        # 结果存储
        self.bookmarks = []
        self.folders = set()
        self.total_folder_counter = 0 # <--- 新增一个计数器
        
        # 状态标志
        self.is_in_a_tag = False
        self.is_in_h3_tag = False
        
        # 临时数据
        self.current_url = ""
        self.current_title = ""
        self.current_folder = ""

    def handle_starttag(self, tag, attrs):
        # 当遇到一个开始标签时被调用, e.g., <a href="...">
        if tag == 'a':
            self.is_in_a_tag = True
            # attrs 是一个 (key, value) 元组列表
            attr_dict = dict(attrs)
            self.current_url = attr_dict.get('href', '')
        elif tag == 'h3':
            self.is_in_h3_tag = True

    def handle_data(self, data):
        # 当遇到标签内的文本时被调用
        if self.is_in_a_tag:
            self.current_title += data
        elif self.is_in_h3_tag:
            self.current_folder += data

    def handle_endtag(self, tag):
        # 当遇到一个结束标签时被调用, e.g., </a>
        if tag == 'a':
            if self.current_url:
                # 1. 解码和规范化URL
                # html.parser 会自动处理HTML实体(& -> &), 我们只需处理百分号编码
                normalized_url = self.current_url
                if self.decode_enabled:
                    normalized_url = unquote(self.current_url)

                # 2. 应用过滤器
                should_add = True
                if self.filter_enabled:
                    if not normalized_url.lower().startswith(('http', 'https', 'ftp')):
                        should_add = False

                # 3. 添加到结果列表
                if should_add:
                    clean_title = self.current_title.strip()
                    if self.mode == 'url':
                        self.bookmarks.append(normalized_url)
                    elif self.mode == 'url-title':
                        self.bookmarks.append((normalized_url, clean_title))
            
            # 4. 重置状态
            self.is_in_a_tag = False
            self.current_url = ""
            self.current_title = ""
            
        elif tag == 'h3':
            self.total_folder_counter += 1 # <--- 每遇到一个</h3>就+1
            folder_name = self.current_folder.strip()
            if folder_name:
                self.folders.add(folder_name)
            self.is_in_h3_tag = False
            self.current_folder = ""

def parse_bookmarks_file_fast(filepath, mode, filter_enabled, decode_enabled):
    """
    【高性能版】使用 html.parser 进行流式解析。
    """
    print(f"正在以 'html.parser 高性能' 模式解析文件: {filepath} (过滤: {'启用' if filter_enabled else '禁用'}, 解码: {'启用' if decode_enabled else '禁用'}) ...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{filepath}' 未找到。")
        return None, 0, None, 0
    except Exception as e:
        print(f"读取或解析文件 '{filepath}' 时出错: {e}")
        return None, 0, None, 0

    # 实例化并运行解析器
    parser = BookmarkParser(mode, filter_enabled, decode_enabled)
    parser.feed(content) # 这是核心步骤，启动流式解析

    # 从解析器实例中获取结果
    all_valid_bookmarks = parser.bookmarks
    folders_set = parser.folders
    # 【修正】从新的计数器获取精确总数
    total_folders_count = parser.total_folder_counter 
    total_bookmarks_count = len(all_valid_bookmarks)
    bookmarks_set = set(all_valid_bookmarks)

    print(f"解析完成: 找到 {total_bookmarks_count} 个书签 ({len(bookmarks_set)}个唯一), "
          f"{total_folders_count} 个文件夹 ({len(folders_set)}个唯一)。")
    
    # 为了与您原有的函数返回格式保持一致
    return bookmarks_set, total_bookmarks_count, folders_set, total_folders_count

def analyze_multiple_files(files, compare_mode, analysis_mode, filter_enabled, decode_enabled):
    # 【功能补全】此函数逻辑与正则版完全一致，现已补全文件夹比较
    start_time = time.time()
    
    all_data = {}
    for f in files:
        b_set, b_total, f_set, f_total = parse_bookmarks_file_fast(f, compare_mode, filter_enabled, decode_enabled)
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
    report_lines.append("        多书签文件对比分析报告 (流式解析版)")
    report_lines.append("=" * 60)
    report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"对比模式: {compare_mode}")
    report_lines.append(f"分析模式: {analysis_mode}")
    report_lines.append(f"协议过滤: {'已启用 (只保留http,https,ftp)' if filter_enabled else '已禁用 (保留所有链接)'}")
    report_lines.append(f"URL 解码: {'已启用' if decode_enabled else '已禁用 (使用原始URL)'}")
    report_lines.append("-" * 60)
    report_lines.append("【输入文件统计】\n")
    for filepath, data in all_data.items():
        report_lines.append(f"文件: {os.path.basename(filepath)}")
        report_lines.append(f"  - 总书签数: {data['b_total']} (唯一: {len(data['b_set'])})")
        report_lines.append(f"  - 总文件夹数: {data['f_total']} (唯一: {len(data['f_set'])})")
    report_lines.append("-" * 60)

    if analysis_mode == 'intersection':
        file_list = list(all_data.keys())
        common_bookmarks = all_data[file_list[0]]['b_set'].copy()
        common_folders = all_data[file_list[0]]['f_set'].copy()
        
        for i in range(1, len(file_list)):
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
            other_folders_union = set()
            for j, other_filepath in enumerate(all_filepaths):
                if i == j: continue
                other_bookmarks_union.update(all_data[other_filepath]['b_set'])
                other_folders_union.update(all_data[other_filepath]['f_set'])
            
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
    parser = argparse.ArgumentParser(description="【流式解析版】比较多个HTML书签文件，分析它们的交集或独有项。", formatter_class=argparse.RawTextHelpFormatter)
    
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
        help="【可选】启用协议过滤，只统计 http, https, ftp 协议的书签。\n"
             "         (默认不启用，即统计所有链接)。"
    )
    parser.add_argument(
        "-d", "--decode",
        action='store_true',
        help="【可选】启用URL解码，处理 %%编码 和 & 等HTML实体。\n"
             "         (默认不启用，直接使用原始URL进行比较)。"
    )
    
    args = parser.parse_args()
    if len(args.files) < 2:
        print("错误: 请至少提供两个文件进行对比。")
        return
    analyze_multiple_files(args.files, args.compare_mode, args.analysis, args.filter, args.decode)

if __name__ == '__main__':
    main()