import argparse
import re
from collections import defaultdict
import time

def find_and_process_duplicates(file_path, output_file=None, report_file=None):
    """
    使用正则表达式高速查找并报告 HTML 书签文件中的重复 URL。
    可选功能：将去重后的书签保存到新文件，将分析报告保存到TXT文件。
    """
    # 屏幕上打印进度信息
    print(f"正在读取文件: '{file_path}'...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：文件 '{file_path}' 未找到。")
        return
    except Exception as e:
        print(f"读取文件时出错：{e}")
        return

    print("文件读取完毕，开始高速解析...")
    start_time = time.time()
    pattern = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', re.IGNORECASE)
    all_bookmarks = pattern.findall(content)
    
    total_bookmarks = len(all_bookmarks)
    parsing_time = time.time() - start_time
    print(f"解析完成！共找到 {total_bookmarks} 个书签 (耗时: {parsing_time:.2f} 秒)。")
    
    if not all_bookmarks:
        print("未在该文件中找到任何书签链接。")
        return

    print("正在统计重复项...")
    url_counts = defaultdict(int)
    url_to_names = defaultdict(list)
    unique_bookmarks_to_save = []
    seen_urls = set()

    for url, name in all_bookmarks:
        clean_name = re.sub(r'<.*?>', '', name).strip()
        url_counts[url] += 1
        url_to_names[url].append(clean_name)
        
        if output_file and url not in seen_urls:
            unique_bookmarks_to_save.append((url, clean_name))
            seen_urls.add(url)

    duplicates = {url: count for url, count in url_counts.items() if count > 1}
    print("统计完成！")

    # === 开始生成报告内容 (新逻辑) ===
    report_lines = []
    report_lines.append("="*40)
    
    if not duplicates:
        report_lines.append("恭喜！在您的书签中未发现重复的链接。")
    else:
        report_lines.append(f"发现 {len(duplicates)} 个重复的 URL：\n")
        sorted_duplicates = sorted(duplicates.items(), key=lambda item: item[1], reverse=True)
        
        for url, count in sorted_duplicates:
            report_lines.append(f"URL: {url}")
            report_lines.append(f"  -> 重复次数: {count}")
            report_lines.append(f"  -> 关联的书签名称:")
            for name in url_to_names[url]:
                report_lines.append(f"    - {name}")
            report_lines.append("-" * 20)

    # === 根据参数决定如何处理报告内容 ===
    if report_file:
        # 如果指定了报告文件，则将报告写入文件
        print(f"正在将分析报告写入 '{report_file}'...")
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print("报告文件已成功保存！")
        except Exception as e:
            print(f"写入报告文件时出错: {e}")
    else:
        # 否则，直接在屏幕上打印
        print('\n'.join(report_lines))

    # 处理去重后的HTML文件 (逻辑不变)
    if output_file:
        print("="*40 + f"\n正在将 {len(unique_bookmarks_to_save)} 个独立书签保存到 '{output_file}'...")
        # ... (此处代码与上一版本完全相同，为简洁省略) ...
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("<!DOCTYPE NETSCAPE-Bookmark-file-1>\n<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">\n<TITLE>Bookmarks</TITLE>\n<H1>Bookmarks</H1>\n<DL><p>\n")
                for url, name in unique_bookmarks_to_save:
                    escaped_url = url.replace('&', '&amp;').replace('"', '&quot;')
                    escaped_name = name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    f.write(f'    <DT><A HREF="{escaped_url}">{escaped_name}</A>\n')
                f.write("</DL><p>\n")
            print("去重后的书签文件已成功保存！")
        except Exception as e:
            print(f"保存去重文件时出错：{e}")


def main():
    parser = argparse.ArgumentParser(
        description="使用正则表达式高速查找 HTML 书签文件中的重复 URL。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("file", help="要检查的 HTML 书签文件的路径。")
    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        help="【可选】指定一个 HTML 文件名，用于保存去重后的书签。\n例如: -o clean_bookmarks.html",
        metavar="OUTPUT_FILE"
    )
    # 新增的参数
    parser.add_argument(
        "-r", "--report",
        dest="report_file",
        help="【可选】指定一个 TXT 文件名，用于保存重复项的分析报告。\n例如: -r duplicate_report.txt",
        metavar="REPORT_FILE"
    )
    
    args = parser.parse_args()
    find_and_process_duplicates(args.file, args.output_file, args.report_file)

if __name__ == '__main__':
    main()