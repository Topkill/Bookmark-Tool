import argparse
import re
import time
from datetime import datetime

def parse_bookmarks_file(filepath, mode):
    """
    使用正则表达式高速解析一个 HTML 书签文件。
    根据指定的模式，返回包含书签信息和文件夹名称的集合。
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

    # 提取文件夹名称的正则表达式 (所有模式通用)
    folder_pattern = re.compile(r'<h3[^>]*>(.*?)</h3>', re.IGNORECASE)
    raw_folders = folder_pattern.findall(content)
    folders = set(re.sub(r'<.*?>', '', f).strip() for f in raw_folders)
    
    bookmarks = set()
    if mode == 'url':
        # 模式1: 只提取 URL
        url_pattern = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\']', re.IGNORECASE)
        bookmarks = set(url_pattern.findall(content))
    elif mode == 'url-title':
        # 模式2: 提取 URL 和标题的组合 (元组)
        bookmark_pattern = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', re.IGNORECASE)
        raw_bookmarks = bookmark_pattern.findall(content)
        for url, title in raw_bookmarks:
            clean_title = re.sub(r'<.*?>', '', title).strip()
            bookmarks.add((url, clean_title)) # 将 (url, title) 元组存入集合

    print(f"解析完成: 找到 {len(bookmarks)} 个书签, {len(folders)} 个文件夹。")
    return bookmarks, folders

def generate_report(file1, file2, output_file, mode):
    """
    比较两个书签文件并根据指定模式生成差异报告。
    """
    start_time = time.time()
    
    # 解析两个文件
    bookmarks1, folders1 = parse_bookmarks_file(file1, mode)
    if bookmarks1 is None: return

    bookmarks2, folders2 = parse_bookmarks_file(file2, mode)
    if bookmarks2 is None: return

    print("\n正在进行差异比较...")
    
    # 集合运算对于字符串集合和元组集合同样有效
    bookmarks_only_in_1 = bookmarks1 - bookmarks2
    bookmarks_only_in_2 = bookmarks2 - bookmarks1
    
    folders_only_in_1 = folders1 - folders2
    folders_only_in_2 = folders2 - folders1

    print("比较完成，正在生成报告...")
    
    # 创建报告内容
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("          书签文件差异分析报告")
    report_lines.append("=" * 60)
    report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"文件 A: {file1}")
    report_lines.append(f"文件 B: {file2}")
    report_lines.append(f"比较模式: {mode}")
    report_lines.append("-" * 60)
    
    # --- 文件夹差异 (逻辑不变) ---
    report_lines.append(f"\n【文件夹差异】\n")
    report_lines.append(f"--- 在 '{file1}' 中存在，但在 '{file2}' 中缺失的文件夹 ({len(folders_only_in_1)}个) ---")
    if folders_only_in_1:
        for folder in sorted(list(folders_only_in_1)): report_lines.append(f"  - {folder}")
    else: report_lines.append("  (无)")
    
    report_lines.append(f"\n--- 在 '{file2}' 中存在，但在 '{file1}' 中缺失的文件夹 ({len(folders_only_in_2)}个) ---")
    if folders_only_in_2:
        for folder in sorted(list(folders_only_in_2)): report_lines.append(f"  - {folder}")
    else: report_lines.append("  (无)")
    report_lines.append("\n" + "=" * 60)

    # --- 书签差异 (根据模式调整输出格式) ---
    report_lines.append(f"\n【书签差异】\n")
    report_lines.append(f"--- 在 '{file1}' 中存在，但在 '{file2}' 中缺失的书签 ({len(bookmarks_only_in_1)}个) ---")
    if bookmarks_only_in_1:
        # 对元组排序时，它会先按第一个元素(url)排，再按第二个元素(title)排
        for item in sorted(list(bookmarks_only_in_1)):
            if mode == 'url-title':
                url, title = item
                report_lines.append(f"  - [ {title} ] {url}")
            else: # mode == 'url'
                report_lines.append(f"  - {item}")
    else: report_lines.append("  (无)")
        
    report_lines.append(f"\n--- 在 '{file2}' 中存在，但在 '{file1}' 中缺失的书签 ({len(bookmarks_only_in_2)}个) ---")
    if bookmarks_only_in_2:
        for item in sorted(list(bookmarks_only_in_2)):
            if mode == 'url-title':
                url, title = item
                report_lines.append(f"  - [ {title} ] {url}")
            else: # mode == 'url'
                report_lines.append(f"  - {item}")
    else: report_lines.append("  (无)")
    report_lines.append("\n" + "=" * 60)
    
    # 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f: f.write('\n'.join(report_lines))
        total_time = time.time() - start_time
        print(f"\n报告 '{output_file}' 已成功生成！总耗时: {total_time:.2f} 秒。")
    except Exception as e: print(f"写入报告文件时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="比较两个HTML书签文件，找出它们之间的差异并生成报告。", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("file1", help="第一个书签文件 (文件A) 的路径。")
    parser.add_argument("file2", help="第二个书签文件 (文件B) 的路径。")
    parser.add_argument("-o", "--output", dest="output_file", required=True, help="【必须】指定用于保存差异报告的 TXT 文件名。\n例如: -o diff_report.txt", metavar="REPORT_FILE")
    # 新增模式选择参数
    parser.add_argument(
        "-m", "--mode",
        choices=['url', 'url-title'],
        default='url',
        help="选择书签的比较模式 (默认为: url)。\n"
             "  url:       只比较链接地址(URL)。\n"
             "  url-title: 严格比较链接地址(URL)和标题。",
    )
    
    args = parser.parse_args()
    generate_report(args.file1, args.file2, args.output_file, args.mode)

if __name__ == '__main__':
    main()