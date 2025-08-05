import argparse
import json
import html
import os
import glob

def convert_single_file(input_file, output_file):
    """
    将单个JSON书签文件转换为HTML格式。
    这是核心的转换逻辑。
    """
    print(f"-> 正在加载: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"   错误: 无法读取或解析文件。 {e}")
        return False

    print("   ...加载成功，开始写入HTML...")
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
    except Exception as e:
        print(f"   错误: 写入HTML文件时失败。 {e}")
        return False
    
    print(f"   成功 -> {output_file}")
    return True

def process_node_recursive(node, out_file, indent_level):
    """
    (与上一版相同) 递归处理一个节点（文件夹或书签）。
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
    批量转换的主函数。
    """
    # 1. 发现所有需要处理的文件
    files_to_process = set()
    for pattern in input_patterns:
        # glob.glob 支持 * 和 ? 等通配符
        found_files = glob.glob(pattern)
        if not found_files:
            print(f"警告: 模式 '{pattern}' 没有匹配到任何文件。")
        files_to_process.update(found_files)

    if not files_to_process:
        print("未找到任何需要处理的文件。程序退出。")
        return

    print(f"\n发现 {len(files_to_process)} 个文件需要转换。")
    print("-" * 50)

    success_count = 0
    failure_count = 0

    # 2. 循环处理每个文件
    for input_path in sorted(list(files_to_process)):
        # 决定输出目录
        if output_dir_path:
            # 如果指定了输出目录，则使用它
            final_output_dir = output_dir_path
        else:
            # 否则，保存在原文件所在的目录
            final_output_dir = os.path.dirname(input_path)

        # 构建输出文件名
        base_name = os.path.basename(input_path)
        file_name_without_ext, _ = os.path.splitext(base_name)
        output_name = file_name_without_ext + '.html'
        output_path = os.path.join(final_output_dir, output_name)

        # 调用核心转换函数
        if convert_single_file(input_path, output_path):
            success_count += 1
        else:
            failure_count += 1
    
    print("-" * 50)
    print("批量转换完成！")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {failure_count} 个文件")


def main():
    parser = argparse.ArgumentParser(
        description="批量将JSON格式的书签文件转换为浏览器可导入的HTML格式。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_patterns", 
        nargs='+', 
        help="一个或多个输入文件/模式。\n"
             "可以使用通配符 * 来匹配多个文件。\n"
             "示例:\n"
             "  C:\\Users\\Me\\Bookmarks_2023.json  (单个文件)\n"
             "  './backups/*.json'                 (当前目录下所有json文件，注意使用引号)\n"
             "  './**/Bookmarks'                   (递归查找所有名为Bookmarks的文件)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="【可选】指定一个统一的目录来存放所有转换后的HTML文件。\n"
             "如果未提供，HTML文件将保存在与其对应的JSON文件相同的目录中。",
        metavar="DIRECTORY"
    )
    
    args = parser.parse_args()
    batch_convert(args.input_patterns, args.output_dir)

if __name__ == '__main__':
    main()