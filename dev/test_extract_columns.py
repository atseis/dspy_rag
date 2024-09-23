import re

def extract_columns_and_comments(sql_content):
    # 正则表达式匹配列定义
    column_pattern = re.compile(r'`(\w+)`\s+\w+\s*(\(\d+\))?(\s+CHARACTER SET \w+ COLLATE \w+)?\s*(NOT NULL)?\s*(AUTO_INCREMENT)?\s*(COMMENT \'(.*?)\')?,?', re.IGNORECASE)
    
    columns_and_comments = []
    for match in column_pattern.finditer(sql_content):
        column_name = match.group(1)
        comment = match.group(7) if match.group(7) else column_name
        columns_and_comments.append(comment)
    
    return columns_and_comments

# 示例SQL内容
sql_content = """
DROP TABLE IF EXISTS `access_role_authority`;
CREATE TABLE `access_role_authority`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `role_code` varchar(32) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL COMMENT '角色名称',
  `target` varchar(64) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL COMMENT '权限目标',
  `action` varchar(64) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 622 CHARACTER SET = utf8 COLLATE = utf8_bin COMMENT = '运营角色权限表' ROW_FORMAT = DYNAMIC;
"""

# 提取列名和注释
columns_and_comments = extract_columns_and_comments(sql_content)
print(columns_and_comments)