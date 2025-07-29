import argparse
import re
import time
from datetime import datetime
import os

def parse_bookmarks(filepath):
    """(不变) 使用正则表达式高速解析HTML书签文件。"""
    print(f"正在解析文件: {filepath} ...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{filepath}' 未找到。")
        return None
    except Exception as e:
        print(f"读取或解析文件时出错: {e}")
        return None
    pattern = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', re.IGNORECASE)
    raw_bookmarks = pattern.findall(content)
    bookmarks_list = [(url, re.sub(r'<.*?>', '', title).strip()) for url, title in raw_bookmarks]
    print(f"解析完成: 共找到 {len(bookmarks_list)} 个书签。")
    return bookmarks_list

def deduplicate_and_generate_report(filepath, mode):
    """
    主函数，执行去重、生成报告和创建新HTML文件。
    """
    start_time = time.time()
    
    print(f"正在处理文件: {os.path.basename(filepath)}")
    
    all_bookmarks = parse_bookmarks(filepath)
    if all_bookmarks is None:
        return

    print(f"正在以 '{mode}' 模式进行去重分析...")

    unique_bookmarks = []
    processed_items = {} 

    for url, title in all_bookmarks:
        key = url if mode == 'url' else (url, title)

        if key not in processed_items:
            original_item = (url, title)
            unique_bookmarks.append(original_item)
            processed_items[key] = {'original': original_item, 'removed': []}
        else:
            processed_items[key]['removed'].append((url, title))

    duplicate_groups = {k: v for k, v in processed_items.items() if v['removed']}

    print(f"分析完成: 发现 {len(duplicate_groups)} 个重复组，共 {sum(len(v['removed']) for v in duplicate_groups.values())} 个重复项将被移除。")
    print("正在生成报告和新文件...")

    report_filename = generate_report_file(filepath, duplicate_groups, mode)
    print(f"--> 详细报告已生成: {report_filename}")

    # 【修改】调用生成干净文件的函数时，传入 mode 参数
    clean_html_filename = generate_clean_html_file(filepath, unique_bookmarks, mode)
    print(f"--> 去重后的新书签文件已生成: {clean_html_filename}")

    total_time = time.time() - start_time
    print(f"\n所有操作完成！总耗时: {total_time:.2f} 秒。")

def generate_report_file(original_filepath, duplicate_groups, mode):
    """
    生成详细的TXT报告文件。
    【已更新摘要信息的显示】
    """
    base_name = os.path.basename(original_filepath)
    file_name_without_ext, _ = os.path.splitext(base_name)
    report_filename = f"{file_name_without_ext}_report_{mode}.txt"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n          书签去重分析报告\n" + "=" * 70 + "\n")
        f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"源文件: {original_filepath}\n")
        f.write(f"去重模式: {mode}\n")

        # --- 这里是修改的部分 ---
        # 1. 先计算总的待移除项数量
        total_removed_items = sum(len(v['removed']) for v in duplicate_groups.values())
        # 2. 在写入时包含这个新信息
        f.write(f"分析结果: 发现 {len(duplicate_groups)} 个重复组，共 {total_removed_items} 个重复项将被移除。\n")
        # --- 修改结束 ---
        
        f.write("-" * 70 + "\n\n")

        if not duplicate_groups:
            f.write("恭喜！未在文件中发现任何重复项。\n")
        else:
            group_count = 0
            sorted_groups = sorted(duplicate_groups.items(), key=lambda item: len(item[1]['removed']), reverse=True)
            
            for key, group_data in sorted_groups:
                group_count += 1
                original_item = group_data['original']
                removed_items = group_data['removed']

                f.write(f"--- 重复组 {group_count}/{len(duplicate_groups)} (本组共 {len(removed_items) + 1} 个) ---\n")
                f.write(f"【保留项】 (文件中第一个出现的版本)\n")
                f.write(f"  - 标题: {original_item[1]}\n")
                f.write(f"  - URL:  {original_item[0]}\n\n")

                f.write(f"【移除的重复项 ({len(removed_items)}个)】\n")
                for url, title in removed_items:
                    f.write(f"  - 标题: {title}\n  - URL:  {url}\n")
                f.write("\n" + "-" * 50 + "\n\n")
    return report_filename

def generate_clean_html_file(original_filepath, unique_bookmarks, mode):
    """
    根据去重后的列表生成新的HTML文件。
    【文件名命名规则已修改】
    """
    base_name = os.path.basename(original_filepath)
    file_name_without_ext, _ = os.path.splitext(base_name)
    # 新的文件名格式，例如: my_bookmarks_cleaned_url.html
    clean_filename = f"{file_name_without_ext}_cleaned_{mode}.html"
    
    with open(clean_filename, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE NETSCAPE-Bookmark-file-1>\n")
        f.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
        f.write(f"<TITLE>Bookmarks (Cleaned - {mode} mode)</TITLE>\n")
        f.write(f"<H1>Bookmarks (Cleaned - {mode} mode)</H1>\n")
        f.write("<DL><p>\n")
        for url, name in unique_bookmarks:
            escaped_url = url.replace('&', '&amp;').replace('"', '&quot;')
            escaped_name = name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            f.write(f'    <DT><A HREF="{escaped_url}">{escaped_name}</A>\n')
        f.write("</DL><p>\n")
    return clean_filename

def main():
    """(不变) 命令行接口"""
    parser = argparse.ArgumentParser(
        description="【最终版】清理HTML书签文件中的重复项，生成与模式对应的干净新文件和详细报告。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("file", help="要处理的HTML书签文件路径。")
    parser.add_argument(
        "-m", "--mode",
        choices=['url', 'url-title'],
        default='url',
        help="选择去重模式 (默认为: url)。\n"
             "  url:       只根据链接地址(URL)判断重复。\n"
             "  url-title: 严格模式，URL和标题都需相同才算重复。",
    )
    
    args = parser.parse_args()
    deduplicate_and_generate_report(args.file, args.mode)

if __name__ == '__main__':
    main()