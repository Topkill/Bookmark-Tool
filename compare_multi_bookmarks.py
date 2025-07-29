import argparse
import re
import time
from datetime import datetime

def parse_bookmarks_file(filepath, mode):
    """
    (无需修改) 使用正则表达式高速解析一个 HTML 书签文件。
    返回包含书签信息和文件夹名称的集合。
    """
    print(f"正在以 '{mode}' 模式解析文件: {filepath} ...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{filepath}' 未找到。")
        return None, None
    except Exception as e:
        print(f"读取文件 '{filepath}' 时出错: {e}")
        return None, None

    folder_pattern = re.compile(r'<h3[^>]*>(.*?)</h3>', re.IGNORECASE)
    raw_folders = folder_pattern.findall(content)
    folders = set(re.sub(r'<.*?>', '', f).strip() for f in raw_folders)
    
    bookmarks = set()
    if mode == 'url':
        url_pattern = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\']', re.IGNORECASE)
        bookmarks = set(url_pattern.findall(content))
    elif mode == 'url-title':
        bookmark_pattern = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', re.IGNORECASE)
        raw_bookmarks = bookmark_pattern.findall(content)
        for url, title in raw_bookmarks:
            clean_title = re.sub(r'<.*?>', '', title).strip()
            bookmarks.add((url, clean_title))

    print(f"解析完成: 找到 {len(bookmarks)} 个书签, {len(folders)} 个文件夹。")
    return bookmarks, folders

def format_bookmark(item, mode):
    """根据模式格式化书签输出。"""
    if mode == 'url-title':
        url, title = item
        return f"  - [ {title} ] {url}"
    return f"  - {item}"

def generate_multi_report(filepaths, output_file, mode):
    """
    比较多个书签文件并生成统一的分析报告。
    """
    start_time = time.time()
    
    # 1. 解析所有文件并存储数据
    all_data = {}
    for fp in filepaths:
        bookmarks, folders = parse_bookmarks_file(fp, mode)
        if bookmarks is None: return
        all_data[fp] = {'bookmarks': bookmarks, 'folders': folders}

    print("\n所有文件解析完毕，开始进行交叉比较分析...")

    # 2. 分析数据
    # 找出所有文件共有的项
    all_bookmark_sets = [d['bookmarks'] for d in all_data.values()]
    all_folder_sets = [d['folders'] for d in all_data.values()]
    
    common_bookmarks = set.intersection(*all_bookmark_sets)
    common_folders = set.intersection(*all_folder_sets)

    # 为每个文件找出其独有的项
    unique_items = {}
    for fp in filepaths:
        # 其他所有文件的书签集合的并集
        other_bookmarks_union = set().union(*(d['bookmarks'] for f, d in all_data.items() if f != fp))
        # 其他所有文件的文件夹集合的并集
        other_folders_union = set().union(*(d['folders'] for f, d in all_data.items() if f != fp))
        
        unique_bookmarks = all_data[fp]['bookmarks'] - other_bookmarks_union
        unique_folders = all_data[fp]['folders'] - other_folders_union
        unique_items[fp] = {'bookmarks': unique_bookmarks, 'folders': unique_folders}

    print("分析完成，正在生成报告...")
    
    # 3. 生成报告
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("          多书签文件交叉对比分析报告")
    report_lines.append("=" * 70)
    report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"比较模式: {mode}")
    report_lines.append("\n参与比较的文件列表:")
    for fp in filepaths:
        report_lines.append(f"  - {fp} ({len(all_data[fp]['bookmarks'])}个书签, {len(all_data[fp]['folders'])}个文件夹)")
    report_lines.append("-" * 70)

    # --- 共同项 ---
    report_lines.append(f"\n【共同项分析：在所有 {len(filepaths)} 个文件中都存在的项目】\n")
    report_lines.append(f"--- 共同的文件夹 ({len(common_folders)}个) ---")
    if common_folders:
        for folder in sorted(list(common_folders)): report_lines.append(f"  - {folder}")
    else: report_lines.append("  (无)")
    
    report_lines.append(f"\n--- 共同的书签 ({len(common_bookmarks)}个) ---")
    if common_bookmarks:
        for item in sorted(list(common_bookmarks)): report_lines.append(format_bookmark(item, mode))
    else: report_lines.append("  (无)")
    report_lines.append("\n" + "=" * 70)

    # --- 独有项 ---
    report_lines.append(f"\n【独有项分析：只在单个文件中存在的项目】\n")
    for fp in filepaths:
        unique_b = unique_items[fp]['bookmarks']
        unique_f = unique_items[fp]['folders']
        report_lines.append(f"--- 只在 '{fp}' 中独有的项目 ---")
        report_lines.append(f"  獨有文件夹 ({len(unique_f)}个):")
        if unique_f:
            for folder in sorted(list(unique_f)): report_lines.append(f"    - {folder}")
        else: report_lines.append("    (无)")
        
        report_lines.append(f"  獨有书签 ({len(unique_b)}个):")
        if unique_b:
            for item in sorted(list(unique_b)): report_lines.append(f"  {format_bookmark(item, mode)}")
        else: report_lines.append("    (无)")
        report_lines.append("-" * 50)

    # 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f: f.write('\n'.join(report_lines))
        total_time = time.time() - start_time
        print(f"\n报告 '{output_file}' 已成功生成！总耗时: {total_time:.2f} 秒。")
    except Exception as e: print(f"写入报告文件时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="比较多个HTML书签文件，找出它们的共同项和独有项。", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("files", nargs='+', help="需要比较的一个或多个书签文件路径 (至少提供两个)。")
    parser.add_argument("-o", "--output", dest="output_file", required=True, help="【必须】指定用于保存分析报告的 TXT 文件名。", metavar="REPORT_FILE")
    parser.add_argument("-m", "--mode", choices=['url', 'url-title'], default='url', help="选择书签的比较模式 (默认为: url)。\n  url:       只比较链接地址(URL)。\n  url-title: 严格比较链接地址(URL)和标题。")
    
    args = parser.parse_args()
    if len(args.files) < 2:
        parser.error("必须提供至少两个文件进行比较。")
    
    generate_multi_report(args.files, args.output_file, args.mode)

if __name__ == '__main__':
    main()