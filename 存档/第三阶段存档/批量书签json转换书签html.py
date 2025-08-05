import argparse
import json
import html
import os
import glob

def count_bookmarks_recursive(node):
    """
    递归地只计算一个节点及其子节点中书签（url类型）的数量。
    """
    count = 0
    # 如果当前节点是URL，计数+1
    if node.get('type') == 'url':
        count = 1
    
    # 如果当前节点有子节点（即文件夹），则递归地将子节点的计数加总
    # 注意：文件夹本身不计入总数
    for child in node.get('children', []):
        count += count_bookmarks_recursive(child)
        
    return count

def write_html_from_data(data, output_file):
    """
    根据已加载的JSON数据，生成HTML书签文件。
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as out_f:
            # 写入HTML头部
            out_f.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
            out_f.write('<TITLE>Bookmarks</TITLE>\n<H1>Bookmarks</H1>\n<DL><p>\n')

            # 递归处理所有节点
            roots = data.get('roots', {})
            for root_name, root_node in roots.items():
                process_node_recursive(root_node, out_f, 1)

            out_f.write('</DL><p>\n')
        return True
    except Exception as e:
        print(f"   错误: 写入HTML文件 '{output_file}' 时失败。 {e}")
        return False

def process_node_recursive(node, out_file, indent_level):
    """
    (与上一版相同) 递归地将节点写入HTML文件。
    """
    indent = "    " * indent_level
    node_type = node.get('type')

    if node_type == 'folder':
        name = html.escape(node.get('name', ''), quote=True)
        date_added = node.get('date_added', '0')[:10]
        out_file.write(f'{indent}<DT><H3 ADD_DATE="{date_added}">{name}</H3>\n')
        out_file.write(f'{indent}<DL><p>\n')
        for child in node.get('children', []):
            process_node_recursive(child, out_file, indent_level + 1)
        out_file.write(f'{indent}</DL><p>\n')

    elif node_type == 'url':
        url = html.escape(node.get('url', ''), quote=True)
        name = html.escape(node.get('name', ''), quote=True)
        date_added = node.get('date_added', '0')[:10]
        out_file.write(f'{indent}<DT><A HREF="{url}" ADD_DATE="{date_added}">{name}</A>\n')

def batch_convert(input_patterns, output_dir_path):
    """
    批量转换的主函数，采用新的文件名生成逻辑。
    """
    # 1. 发现所有需要处理的文件
    files_to_process = set()
    for pattern in input_patterns:
        found_files = glob.glob(pattern, recursive=True)
        if not found_files:
            print(f"警告: 模式 '{pattern}' 没有匹配到任何文件。")
        files_to_process.update(found_files)

    if not files_to_process:
        print("未找到任何需要处理的文件。程序退出。")
        return

    print(f"\n发现 {len(files_to_process)} 个文件需要转换。")
    print("-" * 50)

    success_count, failure_count = 0, 0

    # 2. 循环处理每个文件
    for input_path in sorted(list(files_to_process)):
        print(f"-> 正在处理: {input_path}")
        # --- 第一步: 加载并计数 ---
        try:
            with open(input_path, 'r', encoding='utf-8-sig',errors='replace') as f:
                data = json.load(f)
            
            bookmark_count = 0
            roots = data.get('roots', {})
            for root_node in roots.values():
                 bookmark_count += count_bookmarks_recursive(root_node)
            
            print(f"   分析完成: 共找到 {bookmark_count} 个书签。")
            if bookmark_count == 0:
                print("   警告: 未在该文件中找到任何书签，将生成一个空的HTML文件。")

        except Exception as e:
            print(f"   错误: 无法读取或分析文件。跳过此文件。 {e}")
            failure_count += 1
            continue

        # --- 第二步: 构建输出路径并处理文件名冲突 ---
        final_output_dir = output_dir_path or os.path.dirname(input_path)
        base_output_name = f"bookmarks_{bookmark_count}.html"
        output_path = os.path.join(final_output_dir, base_output_name)
        
        counter = 1
        while os.path.exists(output_path):
            # 如果文件已存在，则添加后缀 (1), (2)...
            new_name = f"bookmarks_{bookmark_count} ({counter}).html"
            output_path = os.path.join(final_output_dir, new_name)
            counter += 1
        
        if output_path != os.path.join(final_output_dir, base_output_name):
            print(f"   注意: 文件名冲突，将使用新名称 -> {os.path.basename(output_path)}")

        # --- 第三步: 写入HTML文件 ---
        if write_html_from_data(data, output_path):
            success_count += 1
        else:
            failure_count += 1
    
    print("-" * 50)
    print("批量转换完成！")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {failure_count} 个文件")

def main():
    parser = argparse.ArgumentParser(description="批量将JSON格式的书签文件转换为浏览器可导入的HTML格式，并根据书签数量命名。", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("input_patterns", nargs='+', help="一个或多个输入文件/模式。\n可以使用通配符 * 来匹配多个文件 (建议使用引号)。")
    parser.add_argument("-o", "--output-dir", help="【可选】指定一个统一的目录来存放所有转换后的HTML文件。", metavar="DIRECTORY")
    
    args = parser.parse_args()
    batch_convert(args.input_patterns, args.output_dir)

if __name__ == '__main__':
    main()