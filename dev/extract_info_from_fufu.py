import re,json
from qdrant_client import QdrantClient

def extract_table_name(s):
    en = re.search(r'CREATE TABLE `([^`]+)`', s).group(1)
    match = re.search(r'COMMENT\s*=\s*\'([^\']*)\'', s)
    ch = match.group(1) if match else None
    if ch is None:
        print(f"{en}")
    return en, ch

def extract_columns_and_comments(sql_content):
    # 正则表达式匹配列定义
    column_pattern = re.compile(r'`(\w+)`\s+\w+\s*(\(\d+\))?(\s+CHARACTER SET \w+ COLLATE \w+)?\s*(NOT NULL)?\s*(AUTO_INCREMENT)?\s*(COMMENT \'(.*?)\')?,?', re.IGNORECASE)
    
    columns_and_comments = []
    for match in column_pattern.finditer(sql_content):
        column_name = match.group(1)
        comment = match.group(7) if match.group(7) else ""
        if comment:
            columns_and_comments.append(f"{column_name}({comment})")
        else:
            columns_and_comments.append(column_name)
    
    return columns_and_comments

def load_and_split_text(file_path, delimiter="-- ----------------------------"):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用分隔符分割文本
    chunks = content.split(delimiter)
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def extract_info(text_chunks):
    table_dict = {}
    description_dict = {}

    for table in text_chunks[1:]:
        en_table_name, ch_table_name = extract_table_name(table)
        # columns = extract_columns_and_comments(table)
        if ch_table_name is None:
            # description = f"表{en_table_name}，包含内容有：{', '.join(columns)}"
            description = f"表{en_table_name}"
        else:
            description = f"表{en_table_name}({ch_table_name})"
        
        table_dict[en_table_name] = table
        description_dict[en_table_name] = description

    # with open('data/tables.json', 'w', encoding='utf-8') as f:
    #     json.dump(table_dict, f, ensure_ascii=False, indent=4)

    with open('data/descriptions_no_cols.json', 'w', encoding='utf-8') as f:
        json.dump(description_dict, f, ensure_ascii=False, indent=4)

file_path  = './data/fufu_ds.txt'
chunks=load_and_split_text(file_path)
extract_info(chunks)
