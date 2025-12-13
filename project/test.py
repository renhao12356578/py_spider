# check_files.py
import os


def check_structure():
    print("📁 当前目录:", os.getcwd())
    print("\n🔍 检查文件结构:")

    # 检查根目录
    print("\n📂 根目录文件:")
    for item in os.listdir('.'):
        if os.path.isdir(item):
            print(f"  📁 {item}/")
        else:
            print(f"  📄 {item}")

    # 检查static文件夹
    print("\n📂 static/ 文件夹:")
    if os.path.exists('static'):
        for root, dirs, files in os.walk('static'):
            level = root.replace('static', '').count(os.sep)
            indent = '  ' * level
            print(f"{indent}📁 {os.path.basename(root) or 'static'}/")
            subindent = '  ' * (level + 1)
            for file in files:
                print(f"{subindent}📄 {file}")
    else:
        print("  ❌ static文件夹不存在")

    # 检查HTML文件中的引用
    print("\n🔗 检查HTML文件中的引用:")
    html_files = [f for f in os.listdir('template') if f.endswith('.html')]
    for html_file in html_files[:3]:  # 检查前3个
        path = os.path.join('template', html_file)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                css_refs = [line for line in content.split('\n') if '.css' in line]
                js_refs = [line for line in content.split('\n') if '.js' in line]

                print(f"\n📄 {html_file}:")
                for ref in css_refs[:2]:
                    print(f"  CSS引用: {ref.strip()[:60]}...")
                for ref in js_refs[:2]:
                    print(f"  JS引用: {ref.strip()[:60]}...")
        except:
            pass


if __name__ == '__main__':
    check_structure()