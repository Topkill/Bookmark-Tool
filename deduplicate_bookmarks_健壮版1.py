# -*- coding: utf-8 -*-
import argparse
import re
import time
from datetime import datetime
import os
import html
from urllib.parse import unquote

def parse_bookmarks(filepath, decode_enabled):
    """
    【可选解码版】使用正则表达式高速解析HTML书签文件。
    - URL解码功能由开关控制，默认关闭。
    """
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
            url, title = raw_url, raw_title
            # 根据开关决定是否解码
            if decode_enabled:
                url = unquote(html.unescape(raw_url))
                title = html.unescape(raw_title)
            
            clean_title = re.sub(r'<.*?>', '', title, flags=re.DOTALL).strip()
            bookmarks_list.append((url, clean_title))

    print(f"解析完成: 共找到 {len(bookmarks_list)} 个书签。")
    return bookmarks_list

def normalize_url(url, strict_protocol, ignore_slash):
    """根据选项标准化URL以进行比较"""
    if not strict_protocol:
        url = re.sub(r'^https?://', '', url)
    if ignore_slash:
        if '/' in url[url.find('://')+3:]:
            url = url.rstrip('/')
    return url

def deduplicate_and_generate_report(filepath, mode, decode_enabled, strict_protocol, ignore_slash):
    """
    主函数，执行去重。
    """
    start_time = time.time()
    
    print(f"正在处理文件: {os.path.basename(filepath)}")
    
    all_bookmarks = parse_bookmarks(filepath, decode_enabled)
    if all_bookmarks is None:
        return

    total_bookmarks_count = len(all_bookmarks)

    print(f"正在以 '{mode}' 模式进行去重分析...")
    print(f"  - 协议区分: {'严格 (HTTP/HTTPS视为不同)' if strict_protocol else '宽松 (HTTP/HTTPS视为相同，默认)'}")
    print(f"  - 末尾斜杠: {'忽略 (a/b/ 和 a/b视为相同)' if ignore_slash else '区分 (a/b/ 和 a/b视为不同，默认)'}")

    unique_bookmarks = []
    processed_items = {} 

    for url, title in all_bookmarks:
        normalized_url_key = normalize_url(url, strict_protocol, ignore_slash)
        key = normalized_url_key if mode == 'url' else (normalized_url_key, title)

        if key not in processed_items:
            original_item = (url, title)
            unique_bookmarks.append(original_item)
            processed_items[key] = {'original': original_item, 'removed': []}
        else:
            processed_items[key]['removed'].append((url, title))

    remaining_bookmarks_count = len(unique_bookmarks)
    duplicate_groups = {k: v for k, v in processed_items.items() if v['removed']}
    total_removed_items = total_bookmarks_count - remaining_bookmarks_count

    if not duplicate_groups:
        print("\n分析完成: 未发现任何重复项。")
    else:
        print(f"\n分析完成: 发现 {len(duplicate_groups)} 个重复组，共 {total_removed_items} 个重复项将被移除。")
    
    print(f"原始书签总数: {total_bookmarks_count}")
    print(f"去重后剩余书签数: {remaining_bookmarks_count}")

    report_options = {
        'decode_enabled': decode_enabled,
        'strict_protocol': strict_protocol,
        'ignore_slash': ignore_slash
    }

    if not duplicate_groups:
        print("将只生成一份确认报告，不会创建新的HTML文件。")
        report_filename = generate_report_file(filepath, duplicate_groups, mode, report_options, total_bookmarks_count, remaining_bookmarks_count)
        print(f"--> 确认报告已生成: {report_filename}")
    else:
        print("正在生成报告和新的已清理文件...")
        report_filename = generate_report_file(filepath, duplicate_groups, mode, report_options, total_bookmarks_count, remaining_bookmarks_count)
        print(f"--> 详细报告已生成: {report_filename}")

        clean_html_filename = generate_clean_html_file(filepath, unique_bookmarks, mode, report_options)
        print(f"--> 去重后的新书签文件已生成: {clean_html_filename}")

    total_time = time.time() - start_time
    print(f"\n所有操作完成！总耗时: {total_time:.2f} 秒。")

def generate_report_file(original_filepath, duplicate_groups, mode, options, total_bookmarks_count, remaining_bookmarks_count):
    """
    生成详细的TXT报告文件，文件名包含处理选项。
    """
    base_name = os.path.basename(original_filepath)
    file_name_without_ext, _ = os.path.splitext(base_name)
    
    # --- 新增：构建文件名后缀 ---
    filename_suffix_parts = []
    if options['decode_enabled']:
        filename_suffix_parts.append('dec')
    if options['strict_protocol']:
        filename_suffix_parts.append('strictP')
    if options['ignore_slash']:
        filename_suffix_parts.append('noSlash')
    suffix = ('_' + '_'.join(filename_suffix_parts)) if filename_suffix_parts else ''
    
    report_filename = f"{file_name_without_ext}_report_{mode}{suffix}.txt"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n          书签去重分析报告\n" + "=" * 70 + "\n")
        f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"源文件: {original_filepath}\n\n")
        
        f.write("--- 处理选项 ---\n")
        f.write(f"去重模式: {mode}\n")
        f.write(f"URL 解码: {'已启用' if options['decode_enabled'] else '已禁用 (默认)'}\n")
        f.write(f"协议区分: {'严格 (HTTP/HTTPS视为不同)' if options['strict_protocol'] else '宽松 (HTTP/HTTPS视为相同，默认)'}\n")
        f.write(f"末尾斜杠: {'忽略 (a/b/ 和 a/b视为相同)' if options['ignore_slash'] else '区分 (a/b/ 和 a/b视为不同，默认)'}\n\n")
        
        f.write("--- 统计结果 ---\n")
        f.write(f"原始书签总数: {total_bookmarks_count}\n")
        f.write(f"去重后剩余书签数: {remaining_bookmarks_count}\n")
        total_removed_items = total_bookmarks_count - remaining_bookmarks_count
        f.write(f"分析结果: 发现 {len(duplicate_groups)} 个重复组，共 {total_removed_items} 个重复项被移除。\n")
        
        f.write("-" * 70 + "\n\n")

        if not duplicate_groups:
            f.write("恭喜！未在文件中发现任何重复项。\n")
        else:
            f.write("--- 重复项详情 ---\n\n")
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

def generate_clean_html_file(original_filepath, unique_bookmarks, mode, options):
    """
    根据去重后的列表生成新的HTML文件，文件名包含处理选项。
    """
    base_name = os.path.basename(original_filepath)
    file_name_without_ext, _ = os.path.splitext(base_name)

    # --- 新增：构建文件名后缀 ---
    filename_suffix_parts = []
    if options['decode_enabled']:
        filename_suffix_parts.append('dec')
    if options['strict_protocol']:
        filename_suffix_parts.append('strictP')
    if options['ignore_slash']:
        filename_suffix_parts.append('noSlash')
    suffix = ('_' + '_'.join(filename_suffix_parts)) if filename_suffix_parts else ''
    
    clean_filename = f"{file_name_without_ext}_cleaned_{mode}{suffix}.html"
    
    with open(clean_filename, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE NETSCAPE-Bookmark-file-1>\n")
        f.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
        f.write(f"<TITLE>Bookmarks (Cleaned - {mode} mode)</TITLE>\n")
        f.write(f"<H1>Bookmarks (Cleaned - {mode} mode)</H1>\n")
        f.write("<DL><p>\n")
        for url, name in unique_bookmarks:
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
    parser.add_argument(
        "-d", "--decode",
        action='store_true',
        help="【可选】启用URL解码，处理 %%编码 和 & 等HTML实体。\n"
             "         (默认不启用，按原始文本进行去重)。"
    )
    parser.add_argument(
        '--strict-protocol',
        action='store_true',
        help="【可选】严格区分 http 和 https 协议。\n"
             "         (默认不区分，将它们视为相同)。"
    )
    parser.add_argument(
        '--ignore-slash',
        action='store_true',
        help="【可选】忽略URL末尾的斜杠'/'。\n"
             "         (默认区分，例如 'example.com/p' 和 'example.com/p/' 被视为不同)。"
    )
    
    args = parser.parse_args()
    deduplicate_and_generate_report(args.file, args.mode, args.decode, args.strict_protocol, args.ignore_slash)

if __name__ == '__main__':
    main()
