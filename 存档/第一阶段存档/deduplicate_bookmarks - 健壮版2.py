# -*- coding: utf-8 -*-
import argparse
import re
import time
from datetime import datetime
import os
from urllib.parse import unquote
import html # 引入html库以应对未来可能的扩展

def parse_bookmarks(filepath, decode_enabled):
    """
    【可选解码版】使用正则表达式高速解析。
    - URL解码功能由 decode_enabled 开关控制。
    """
    # 在状态报告中也反映出解码的状态
    print(f"正在解析文件: {filepath} (解码: {'启用' if decode_enabled else '禁用'}) ...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{filepath}' 未找到。")
        return None
    except Exception as e:
        print(f"读取或解析文件时出错: {e}")
        return None
        
    pattern = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
    raw_bookmarks = pattern.findall(content)
    
    bookmarks_list = []
    for raw_url, raw_title in raw_bookmarks:
        if raw_url:
            url = raw_url
            # 【核心改动】根据开关决定是否解码
            if decode_enabled:
                # 同时处理HTML实体和百分号编码，确保结果健壮
                url = unquote(html.unescape(raw_url))
            
            # 标题始终进行HTML实体解码，因为标题中的&几乎总是代表&
            clean_title = re.sub(r'<.*?>', '', html.unescape(raw_title), flags=re.DOTALL).strip()
            bookmarks_list.append((url, clean_title))

    print(f"解析完成: 共找到 {len(bookmarks_list)} 个书签。")
    return bookmarks_list

def deduplicate_and_generate_report(filepath, mode, decode_enabled):
    """
    主函数，执行去重。
    """
    start_time = time.time()
    
    print(f"正在处理文件: {os.path.basename(filepath)}")
    
    # 传递解码开关
    all_bookmarks = parse_bookmarks(filepath, decode_enabled)
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

    if not duplicate_groups:
        print("分析完成: 未发现任何重复项。")
        print("将只生成一份确认报告，不会创建新的HTML文件。")
        report_filename = generate_report_file(filepath, duplicate_groups, mode, decode_enabled)
        print(f"--> 确认报告已生成: {report_filename}")
    else:
        total_removed_items = sum(len(v['removed']) for v in duplicate_groups.values())
        print(f"分析完成: 发现 {len(duplicate_groups)} 个重复组，共 {total_removed_items} 个重复项将被移除。")
        print("正在生成报告和新的已清理文件...")

        report_filename = generate_report_file(filepath, duplicate_groups, mode, decode_enabled)
        print(f"--> 详细报告已生成: {report_filename}")

        clean_html_filename = generate_clean_html_file(filepath, unique_bookmarks, mode)
        print(f"--> 去重后的新书签文件已生成: {clean_html_filename}")

    total_time = time.time() - start_time
    print(f"\n所有操作完成！总耗时: {total_time:.2f} 秒。")

def generate_report_file(original_filepath, duplicate_groups, mode, decode_enabled):
    """
    生成详细的TXT报告文件。
    """
    base_name = os.path.basename(original_filepath)
    file_name_without_ext, _ = os.path.splitext(base_name)
    report_filename = f"{file_name_without_ext}_report_{mode}.txt"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n          书签去重分析报告\n" + "=" * 70 + "\n")
        f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"源文件: {original_filepath}\n")
        f.write(f"去重模式: {mode}\n")
        # 在报告中加入解码状态
        f.write(f"URL 解码: {'已启用' if decode_enabled else '已禁用 (默认)'}\n")

        total_removed_items = sum(len(v['removed']) for v in duplicate_groups.values())
        f.write(f"分析结果: 发现 {len(duplicate_groups)} 个重复组，共 {total_removed_items} 个重复项将被移除。\n")
        
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
    使用 html.escape 确保生成的文件格式正确。
    """
    base_name = os.path.basename(original_filepath)
    file_name_without_ext, _ = os.path.splitext(base_name)
    clean_filename = f"{file_name_without_ext}_cleaned_{mode}.html"
    
    with open(clean_filename, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE NETSCAPE-Bookmark-file-1>\n")
        f.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
        f.write(f"<TITLE>Bookmarks (Cleaned - {mode} mode)</TITLE>\n")
        f.write(f"<H1>Bookmarks (Cleaned - {mode} mode)</H1>\n")
        f.write("<DL><p>\n")
        for url, name in unique_bookmarks:
            # 使用标准的html.escape进行编码，比手动替换更安全
            escaped_url = html.escape(url, quote=True)
            escaped_name = html.escape(name)
            f.write(f'    <DT><A HREF="{escaped_url}">{escaped_name}</A>\n')
        f.write("</DL><p>\n")
    return clean_filename

def main():
    parser = argparse.ArgumentParser(
        description="【可选解码版】清理HTML书签文件中的重复项，生成干净的新文件和详细报告。",
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
    
    # 【新增】解码开关，默认为False
    parser.add_argument(
        "-d", "--decode",
        action='store_true',
        help="【可选】启用URL解码，处理 %%编码 和 & 等HTML实体。\n"
             "         (默认不启用，按原始文本进行去重)。"
    )
    
    args = parser.parse_args()
    # 将解码开关传递给主函数
    deduplicate_and_generate_report(args.file, args.mode, args.decode)

if __name__ == '__main__':
    main()
