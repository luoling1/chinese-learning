#!/usr/bin/env python3
"""
练习生成质量的全面测试脚本
测试 /workspace/index.html 中的 JS 代码逻辑
"""

import re
import sys

def read_html():
    with open('/workspace/index.html', 'r', encoding='utf-8') as f:
        return f.read()

html = read_html()

def extract_balanced(text, start_char='{', end_char='}', start_pos=0):
    """Extract balanced braces, respecting single-quoted and double-quoted strings."""
    depth = 0
    i = start_pos
    while i < len(text):
        c = text[i]
        # Skip single-quoted strings
        if c == "'":
            i += 1
            while i < len(text) and text[i] != "'":
                if text[i] == '\\':
                    i += 1
                i += 1
            i += 1
            continue
        # Skip double-quoted strings
        if c == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                if text[i] == '\\':
                    i += 1
                i += 1
            i += 1
            continue
        if c == start_char:
            depth += 1
        elif c == end_char:
            depth -= 1
            if depth == 0:
                return text[start_pos:i+1]
        i += 1
    return None

def extract_templates(html):
    match = re.search(r'function getFillTemplate\(ch\)\s*\{', html)
    if not match:
        print("ERROR: 找不到 getFillTemplate 函数")
        return {}, 0
    func_body = html[match.start():]
    tmpl_match = re.search(r'const templates\s*=\s*\{', func_body)
    if not tmpl_match:
        return {}, 0
    brace_start = func_body.index('{', tmpl_match.start())
    templates_str = extract_balanced(func_body, '{', '}', brace_start)
    if not templates_str:
        return {}, 0

    templates = {}
    char_pattern = re.compile(r"'([^']+)'\s*:\s*\[")
    for cm in char_pattern.finditer(templates_str):
        char_key = cm.group(1)
        arr_start = cm.end() - 1
        arr_str = extract_balanced(templates_str, '[', ']', arr_start)
        if not arr_str:
            continue
        template_list = []
        obj_pattern = re.compile(
            r"question\s*:\s*['\"]([^'\"]+)['\"][^}]*?options\s*:\s*\[([^\]]*)\]")
        for om in obj_pattern.finditer(arr_str):
            question = om.group(1)
            opts_str = om.group(2)
            options = re.findall(r"['\"]([^'\"]+)['\"]", opts_str)
            template_list.append({'question': question, 'options': options})
        templates[char_key] = template_list

    generic_match = re.search(r'const genericTemplates\s*=\s*\[', func_body)
    generic_count = 0
    if generic_match:
        garr_start = func_body.index('[', generic_match.start())
        garr_str = extract_balanced(func_body, '[', ']', garr_start)
        if garr_str:
            generic_count = garr_str.count('{ question:')
    return templates, generic_count

def extract_fixwords(html):
    match = re.search(r'function fixWords\(c\)\s*\{', html)
    if not match:
        return {}
    func_body = html[match.start():]
    cw_match = re.search(r'const commonWords\s*=\s*\{', func_body)
    if not cw_match:
        return {}
    brace_start = func_body.index('{', cw_match.start())
    cw_str = extract_balanced(func_body, '{', '}', brace_start)
    if not cw_str:
        return {}
    commonWords = {}
    for lm in re.finditer(r"'([^']+)'\s*:\s*\[([^\]]*)\]", cw_str):
        words = re.findall(r"['\"]([^'\"]+)['\"]", lm.group(2))
        commonWords[lm.group(1)] = words
    return commonWords

def extract_book_chars(html):
    match = re.search(r'const BOOK_DATA\s*=\s*\{', html)
    if not match:
        return []
    brace_start = html.index('{', match.start())
    book_str = extract_balanced(html, '{', '}', brace_start)
    if not book_str:
        return []
    chars = []
    for nc_match in re.finditer(r'"newChars"\s*:\s*\[', book_str):
        arr_start = book_str.index('[', nc_match.start())
        nc_str = extract_balanced(book_str, '[', ']', arr_start)
        if not nc_str:
            continue
        for cm in re.finditer(
            r'"char"\s*:\s*"([^"]+)"\s*,\s*"pinyin"\s*:\s*"([^"]+)"[^}]*?'
            r'"words"\s*:\s*\[([^\]]*)\]', nc_str):
            words = re.findall(r'"([^"]+)"', cm.group(3))
            chars.append({'char': cm.group(1), 'pinyin': cm.group(2), 'words': words})
    return chars

def check_functions_exist(html):
    functions = {
        'generateDynamicExercises': r'function generateDynamicExercises\s*\(',
        'selectQuizOption': r'function selectQuizOption\s*\(',
        'renderFillExercise': r'function renderFillExercise\s*\(',
        'renderCharToPinyinExercise': r'function renderCharToPinyinExercise\s*\(',
        'renderPinyinToCharExercise': r'function renderPinyinToCharExercise\s*\(',
        'renderReadExercise': r'function renderReadExercise\s*\(',
        'getFillTemplate': r'function getFillTemplate\s*\(',
        'fixWords': r'function fixWords\s*\(',
        'generatePinyinOptions': r'function generatePinyinOptions\s*\(',
        'generateCharOptions': r'function generateCharOptions\s*\(',
        'selectFillOption': r'function selectFillOption\s*\(',
    }
    return {name: bool(re.search(pattern, html)) for name, pattern in functions.items()}

def main():
    print("=" * 70)
    print("  练习生成质量全面测试报告")
    print("=" * 70)
    print()

    templates, generic_count = extract_templates(html)
    commonWords = extract_fixwords(html)
    book_chars = extract_book_chars(html)
    func_results = check_functions_exist(html)
    total_issues = 0

    # ============================================================
    # 测试 1: 答案泄露测试
    # ============================================================
    print("-" * 70)
    print("测试 1: 答案泄露测试")
    print("-" * 70)
    print()

    leaked_count = 0
    leaked_templates = []
    for char_key, tmpl_list in templates.items():
        for tmpl in tmpl_list:
            question = tmpl['question']
            question_text = question.replace('选字填空：', '', 1) if question.startswith('选字填空：') else question
            if char_key in question_text:
                leaked_count += 1
                leaked_templates.append({'char': char_key, 'question': tmpl['question']})

    if leaked_count == 0:
        print("  [PASS] 未发现答案泄露问题")
    else:
        print(f"  [FAIL] 发现 {leaked_count} 个模板存在答案泄露问题：")
        for lt in leaked_templates:
            print(f"    - 字符 '{lt['char']}': \"{lt['question']}\"")
            print(f"      答案 '{lt['char']}' 出现在问题文本中")
        total_issues += leaked_count
    print()

    # ============================================================
    # 测试 2: 答案唯一性测试
    # ============================================================
    print("-" * 70)
    print("测试 2: 答案唯一性测试")
    print("-" * 70)
    print()

    # 检查答案是否在选项中
    answer_not_in_options = []
    for char_key, tmpl_list in templates.items():
        for tmpl in tmpl_list:
            if char_key not in tmpl['options']:
                answer_not_in_options.append({
                    'char': char_key,
                    'question': tmpl['question'],
                    'options': tmpl['options']
                })

    if answer_not_in_options:
        print(f"  [FAIL] 发现 {len(answer_not_in_options)} 个模板答案不在选项中：")
        for a in answer_not_in_options:
            print(f"    - 字符 '{a['char']}': \"{a['question']}\"")
            print(f"      选项: {a['options']} (缺少答案 '{a['char']}')")
        total_issues += len(answer_not_in_options)
    else:
        print("  [PASS] 所有模板的答案都在选项中")
    print()

    # 检查选项中是否有重复
    duplicate_options = []
    for char_key, tmpl_list in templates.items():
        for tmpl in tmpl_list:
            if len(tmpl['options']) != len(set(tmpl['options'])):
                duplicate_options.append({
                    'char': char_key,
                    'question': tmpl['question'],
                    'options': tmpl['options']
                })

    if duplicate_options:
        print(f"  [FAIL] 发现 {len(duplicate_options)} 个模板选项有重复：")
        for d in duplicate_options:
            print(f"    - 字符 '{d['char']}': \"{d['question']}\"")
            print(f"      选项: {d['options']}")
        total_issues += len(duplicate_options)
    else:
        print("  [PASS] 所有模板选项无重复")
    print()

    # 检查易混淆选项组
    # 定义已知的高风险选项组模式
    high_risk_groups = [
        frozenset(['他', '她', '它']),
        frozenset(['我', '你', '他']),
        frozenset(['的', '得', '地']),
        frozenset(['不', '没', '别']),
        frozenset(['很', '最', '太']),
        frozenset(['也', '都', '还']),
        frozenset(['再', '又', '还']),
        frozenset(['才', '就', '已']),
        frozenset(['想', '要', '会']),
        frozenset(['来', '去', '回']),
        frozenset(['对', '错', '好']),
        frozenset(['真', '很', '太']),
        frozenset(['真', '很', '好']),
        frozenset(['新', '旧', '好']),
        frozenset(['老', '新', '好']),
        frozenset(['冷', '热', '暖']),
        frozenset(['热', '冷', '凉']),
        frozenset(['高', '远', '快']),
        frozenset(['多', '少', '大']),
        frozenset(['快', '慢', '远']),
        frozenset(['慢', '快', '少']),
        frozenset(['近', '远', '大']),
        frozenset(['远', '近', '清']),
        frozenset(['远', '近', '高']),
        frozenset(['近', '远', '快']),
        frozenset(['胖', '瘦', '小']),
        frozenset(['瘦', '胖', '弱']),
        frozenset(['美', '丑', '好']),
        frozenset(['重', '轻', '大']),
        frozenset(['轻', '重', '小']),
        frozenset(['力', '气', '量']),
        frozenset(['平', '安', '静']),
        frozenset(['安', '平', '静']),
        frozenset(['思', '想', '念']),
        frozenset(['记', '写', '念']),
        frozenset(['念', '读', '背']),
        frozenset(['念', '读', '学']),
        frozenset(['信', '任', '知']),
        frozenset(['信', '听', '传']),
        frozenset(['答', '问', '说']),
        frozenset(['答', '问', '想']),
        frozenset(['问', '答', '说']),
        frozenset(['问', '答', '想']),
        frozenset(['知', '不', '想']),
        frozenset(['找', '看', '拿']),
        frozenset(['回', '去', '来']),
        frozenset(['回', '答', '问']),
        frozenset(['回', '转', '点']),
        frozenset(['给', '送', '拿']),
        frozenset(['做', '写', '看']),
        frozenset(['做', '玩', '看']),
        frozenset(['用', '拿', '给']),
        frozenset(['用', '花', '费']),
        frozenset(['用', '做', '看']),
        frozenset(['让', '叫', '使']),
        frozenset(['让', '叫', '请']),
        frozenset(['被', '把', '让']),
        frozenset(['把', '将', '被']),
        frozenset(['从', '到', '在']),
        frozenset(['到', '去', '来']),
        frozenset(['到', '去', '在']),
        frozenset(['没', '不', '也']),
        frozenset(['别', '不', '没']),
        frozenset(['只', '有', '没']),
        frozenset(['只', '要', '会']),
        frozenset(['更', '很', '最']),
        frozenset(['第', '一', '这']),
        frozenset(['名', '字', '号']),
        frozenset(['名', '姓', '号']),
        frozenset(['字', '词', '句']),
        frozenset(['文', '字', '书']),
        frozenset(['文', '字', '数']),
        frozenset(['数', '语', '英']),
        frozenset(['数', '读', '写']),
        frozenset(['数', '看', '算']),
        frozenset(['步', '米', '里']),
        frozenset(['步', '脚', '手']),
        frozenset(['动', '走', '跑']),
        frozenset(['平', '陡', '弯']),
        frozenset(['平', '安', '和']),
        frozenset(['安', '平', '保']),
        frozenset(['安', '放', '用']),
        frozenset(['教', '学', '帮']),
        frozenset(['教', '帮', '让']),
        frozenset(['话', '事', '字']),
        frozenset(['语', '话', '文']),
        frozenset(['语', '数', '英']),
        frozenset(['音', '声', '乐']),
        frozenset(['音', '拼', '读']),
        frozenset(['点', '时', '分']),
        frozenset(['点', '摇', '低']),
        frozenset(['点', '买', '做']),
        frozenset(['已', '也', '还']),
        frozenset(['又', '再', '还']),
        frozenset(['又', '是', '也']),
        frozenset(['乐', '欢', '喜']),
        frozenset(['乐', '音', '声']),
        frozenset(['歌', '曲', '戏']),
        frozenset(['歌', '听', '唱']),
        frozenset(['歌', '唱', '跳']),
        frozenset(['园', '院', '校']),
        frozenset(['店', '场', '院']),
        frozenset(['城', '村', '京']),
        frozenset(['城', '村', '墙']),
        frozenset(['村', '城', '店']),
        frozenset(['信', '纸', '书']),
        frozenset(['记', '写', '画']),
        frozenset(['答', '问', '回']),
        frozenset(['长', '短', '远']),
        frozenset(['短', '长', '近']),
        frozenset(['早', '晚', '快']),
        frozenset(['今', '明', '昨']),
        frozenset(['春', '夏', '秋']),
        frozenset(['夏', '春', '冬']),
        frozenset(['秋', '春', '夏']),
        frozenset(['冬', '春', '秋']),
        frozenset(['前', '后', '旁']),
        frozenset(['左', '右', '前']),
        frozenset(['东', '西', '南']),
        frozenset(['南', '北', '东']),
        frozenset(['牛', '羊', '马']),
        frozenset(['猫', '狗', '鸟']),
        frozenset(['鱼', '鸟', '虫']),
        frozenset(['风', '雨', '雪']),
        frozenset(['雨', '雪', '风']),
        frozenset(['河', '海', '湖']),
        frozenset(['路', '街', '桥']),
        frozenset(['床', '桌', '椅']),
        frozenset(['桌', '椅', '床']),
        frozenset(['门', '窗', '墙']),
        frozenset(['书', '笔', '本']),
        frozenset(['笔', '纸', '本']),
        frozenset(['笔', '纸', '书']),
        frozenset(['纸', '笔', '布']),
        frozenset(['纸', '笔', '水']),
        frozenset(['鞋', '袜', '帽']),
        frozenset(['衣', '裤', '鞋']),
        frozenset(['饭', '菜', '水']),
        frozenset(['饭', '菜', '汤']),
        frozenset(['菜', '饭', '肉']),
        frozenset(['菜', '花', '树']),
        frozenset(['花', '草', '树']),
        frozenset(['草', '花', '菜']),
        frozenset(['草', '花', '叶']),
        frozenset(['眼', '耳', '口']),
        frozenset(['眼', '耳', '鼻']),
        frozenset(['手', '脚', '头']),
        frozenset(['脚', '手', '鞋']),
        frozenset(['脚', '手', '头']),
        frozenset(['头', '手', '眼']),
        frozenset(['头', '手', '身']),
        frozenset(['心', '头', '手']),
        frozenset(['车', '船', '飞机']),
        frozenset(['车', '人', '树']),
        frozenset(['球', '牌', '棋']),
        frozenset(['灯', '门', '窗']),
        frozenset(['灯', '亮', '开']),
        frozenset(['灯', '光', '火']),
        frozenset(['钱', '书', '笔']),
        frozenset(['钱', '水', '电']),
        frozenset(['火', '水', '风']),
        frozenset(['火', '水', '电']),
        frozenset(['水', '茶', '饭']),
        frozenset(['水', '鱼', '草']),
        frozenset(['米', '面', '菜']),
        frozenset(['桥', '路', '门']),
        frozenset(['桥', '路', '街']),
        frozenset(['爸', '妈', '哥']),
        frozenset(['妈', '爸', '姐']),
        frozenset(['红', '蓝', '绿']),
        frozenset(['红', '蓝', '白']),
        frozenset(['蓝', '红', '白']),
        frozenset(['蓝', '红', '绿']),
        frozenset(['绿', '红', '黄']),
        frozenset(['白', '黑', '红']),
        frozenset(['白', '黑', '灰']),
        frozenset(['黑', '白', '红']),
        frozenset(['黑', '白', '灰']),
        frozenset(['黄', '红', '绿']),
        frozenset(['黄', '红', '白']),
        frozenset(['云', '风', '雨']),
        frozenset(['云', '风', '鸟']),
        frozenset(['月', '日', '星']),
        frozenset(['星', '月', '云']),
        frozenset(['星', '月', '灯']),
        frozenset(['日', '月', '年']),
        frozenset(['日', '月', '天']),
        frozenset(['年', '月', '天']),
        frozenset(['山', '地', '路']),
        frozenset(['山', '楼', '墙']),
        frozenset(['山', '树', '墙']),
        frozenset(['地', '天', '山']),
        frozenset(['地', '得', '的']),
        frozenset(['天', '地', '山']),
        frozenset(['天', '年', '月']),
        frozenset(['家', '校', '店']),
        frozenset(['校', '店', '家']),
        frozenset(['画', '写', '看']),
        frozenset(['画', '书', '照片']),
        frozenset(['胖', '瘦', '可爱']),
        frozenset(['笑', '哭', '叫']),
        frozenset(['哭', '笑', '叫']),
        frozenset(['走', '跑', '跳']),
        frozenset(['走', '跑', '飞']),
        frozenset(['走', '跑', '来']),
        frozenset(['跑', '走', '跳']),
        frozenset(['跑', '走', '飞']),
        frozenset(['坐', '站', '躺']),
        frozenset(['站', '坐', '走']),
        frozenset(['站', '坐', '躺']),
        frozenset(['读', '看', '写']),
        frozenset(['写', '读', '看']),
        frozenset(['写', '读', '说']),
        frozenset(['写', '读', '做']),
        frozenset(['听', '看', '唱']),
        frozenset(['听', '看', '闻']),
        frozenset(['听', '看', '说']),
        frozenset(['吃', '喝', '买']),
        frozenset(['吃', '喝', '做']),
        frozenset(['喝', '吃', '买']),
        frozenset(['买', '卖', '拿']),
        frozenset(['买', '卖', '看']),
        frozenset(['买', '卖', '吃']),
        frozenset(['爱', '喜欢', '想']),
        frozenset(['爱', '想', '要']),
        frozenset(['爱', '想', '会']),
        frozenset(['玩', '学', '做']),
        frozenset(['玩', '看', '做']),
        frozenset(['玩', '看', '爬']),
        frozenset(['学', '教', '看']),
        frozenset(['学', '做', '写']),
        frozenset(['和', '跟', '给']),
        frozenset(['是', '不是', '也']),
        frozenset(['是', '有', '在']),
        frozenset(['是', '叫', '在']),
        frozenset(['不', '也', '很']),
        frozenset(['不', '很', '也']),
        frozenset(['不', '很', '太']),
        frozenset(['有', '没', '是']),
        frozenset(['这', '那', '哪']),
        frozenset(['那', '这', '哪']),
        frozenset(['大', '小', '好']),
        frozenset(['大', '小', '多']),
        frozenset(['小', '大', '好']),
        frozenset(['小', '大', '快']),
        frozenset(['上', '下', '中']),
        frozenset(['上', '下', '里']),
        frozenset(['来', '去', '走']),
        frozenset(['来', '去', '到']),
        frozenset(['去', '来', '回']),
        frozenset(['说', '读', '写']),
        frozenset(['说', '问', '想']),
        frozenset(['说', '读', '唱']),
        frozenset(['看', '读', '听']),
        frozenset(['看', '读', '写']),
        frozenset(['看', '找', '听']),
        frozenset(['好', '坏', '冷']),
        frozenset(['好', '很', '太']),
        frozenset(['好', '不', '很']),
        frozenset(['会', '能', '想']),
        frozenset(['要', '想', '会']),
        frozenset(['想', '要', '会']),
        frozenset(['想', '要', '看']),
        frozenset(['在', '去', '回']),
        frozenset(['在', '去', '上']),
        frozenset(['在', '去', '来']),
        frozenset(['里', '外', '上']),
        frozenset(['外', '里', '上']),
        frozenset(['王', '皇', '帝']),
        frozenset(['王', '国', '家']),
        frozenset(['果', '树', '花']),
        frozenset(['果', '因', '事']),
        frozenset(['果', '花', '叶']),
        frozenset(['国', '家', '城']),
        frozenset(['国', '京', '城']),
        frozenset(['友', '人', '师']),
        frozenset(['友', '爱', '好']),
        frozenset(['师', '生', '长']),
        frozenset(['校', '店', '家']),
        frozenset(['他', '牛', '羊']),
    ]

    confusing_issues = []
    for char_key, tmpl_list in templates.items():
        for tmpl in tmpl_list:
            opts_frozenset = frozenset(tmpl['options'])
            for hrg in high_risk_groups:
                if opts_frozenset == hrg:
                    # 找到匹配 - 检查答案是否在选项中
                    if char_key not in tmpl['options']:
                        confusing_issues.append({
                            'char': char_key,
                            'question': tmpl['question'],
                            'options': tmpl['options'],
                            'issue': f'答案不在选项中，使用了高风险选项组 {list(hrg)}'
                        })
                    else:
                        # 答案在选项中，但选项组本身容易混淆
                        confusing_issues.append({
                            'char': char_key,
                            'question': tmpl['question'],
                            'options': tmpl['options'],
                            'issue': f'使用了高风险选项组 {list(hrg)}，可能有多个合理答案'
                        })
                    break

    if confusing_issues:
        # 去重
        seen = set()
        unique_issues = []
        for ci in confusing_issues:
            key = (ci['char'], ci['question'])
            if key not in seen:
                seen.add(key)
                unique_issues.append(ci)

        print(f"  [WARN] 发现 {len(unique_issues)} 个模板使用了高风险选项组（可能答案不唯一）：")
        for ui in unique_issues[:30]:  # 最多显示30个
            print(f"    - 字符 '{ui['char']}': \"{ui['question']}\"")
            print(f"      选项: {ui['options']}")
            print(f"      {ui['issue']}")
        if len(unique_issues) > 30:
            print(f"    ... 还有 {len(unique_issues) - 30} 个类似问题")
        total_issues += len(unique_issues)
    else:
        print("  [PASS] 未发现高风险选项组问题")
    print()

    # ============================================================
    # 测试 3: 词汇有效性测试
    # ============================================================
    print("-" * 70)
    print("测试 3: 词汇有效性测试")
    print("-" * 70)
    print()

    all_unique_chars = {}
    for bc in book_chars:
        ch = bc['char']
        if ch not in all_unique_chars:
            all_unique_chars[ch] = bc['words']

    # 3a: 检查 BOOK_DATA 原始 words
    print("  3a. BOOK_DATA 原始 words 数据检查")
    print()
    known_invalid = {'的子', '大了', '是子', '不子', '了子', '我子', '大是', '大不', '大我'}
    invalid_in_book = []
    for ch, words in all_unique_chars.items():
        for w in words:
            if w in known_invalid:
                invalid_in_book.append((ch, w))

    if not invalid_in_book:
        print("    [PASS] BOOK_DATA 中未发现已知无效词")
    else:
        print(f"    [FAIL] BOOK_DATA 中发现 {len(invalid_in_book)} 个已知无效词：")
        for ch, w in invalid_in_book:
            print(f"      - 字符 '{ch}': 词 \"{w}\"")
        total_issues += len(invalid_in_book)
    print()

    # 3b: fixWords 覆盖检查
    print("  3b. fixWords 覆盖情况检查")
    print()
    known_problem_chars = {'的', '是', '不', '了', '我'}
    covered_chars = set(commonWords.keys())
    uncovered = known_problem_chars - covered_chars
    if not uncovered:
        print(f"    [PASS] fixWords 覆盖了所有已知问题字符: {known_problem_chars}")
    else:
        print(f"    [FAIL] fixWords 未覆盖: {uncovered}")
        total_issues += len(uncovered)
    print()

    # 3c: 修复后词汇合理性
    print("  3c. 修复后词汇合理性检查")
    print()
    invalid_in_fix = []
    for ch, words in commonWords.items():
        for w in words:
            if w in known_invalid:
                invalid_in_fix.append((ch, w))
    if not invalid_in_fix:
        print("    [PASS] fixWords 中未发现已知无效词")
    else:
        print(f"    [FAIL] fixWords 中发现已知无效词：")
        for ch, w in invalid_in_fix:
            print(f"      - 字符 '{ch}': 词 \"{w}\"")
        total_issues += len(invalid_in_fix)

    unreasonable = []
    for ch, words in commonWords.items():
        for w in words:
            if len(w) < 2 or len(w) > 4:
                unreasonable.append((ch, w, len(w)))
    if not unreasonable:
        print("    [PASS] fixWords 中所有词长度合理(2-4字)")
    else:
        print(f"    [WARN] fixWords 中发现长度不合理的词：")
        for ch, w, l in unreasonable:
            print(f"      - 字符 '{ch}': 词 \"{w}\" (长度{l})")
        total_issues += len(unreasonable)

    duplicates = []
    for ch, words in commonWords.items():
        if len(words) != len(set(words)):
            dup = [w for w in words if words.count(w) > 1]
            duplicates.append((ch, list(set(dup))))
    if not duplicates:
        print("    [PASS] fixWords 中无重复词")
    else:
        print(f"    [WARN] fixWords 中发现重复词：")
        for ch, d in duplicates:
            print(f"      - 字符 '{ch}': 重复词 {d}")
        total_issues += len(duplicates)
    print()

    # 3d: 默认回退检查
    print("  3d. 默认回退词汇检查")
    print()
    chars_not_in_fix = set(all_unique_chars.keys()) - covered_chars
    if chars_not_in_fix:
        print(f"    [INFO] {len(chars_not_in_fix)} 个字符不在 fixWords 中，使用默认回退: ch+'人', ch+'大', ch+'好'")
        bad_defaults = []
        for ch in sorted(chars_not_in_fix):
            for s in ['人', '大', '好']:
                w = ch + s
                if w in known_invalid:
                    bad_defaults.append((ch, w))
        if not bad_defaults:
            print("    [PASS] 默认回退词汇未发现明显不合理组合")
        else:
            print(f"    [WARN] 默认回退中发现不合理组合：")
            for ch, w in bad_defaults:
                print(f"      - 字符 '{ch}': 词 \"{w}\"")
            total_issues += len(bad_defaults)
    print()

    # ============================================================
    # 测试 4: 练习类型覆盖测试
    # ============================================================
    print("-" * 70)
    print("测试 4: 练习类型覆盖测试")
    print("-" * 70)
    print()

    print("  4a. 关键函数存在性检查")
    print()
    for func_name, exists in func_results.items():
        status = "[PASS]" if exists else "[FAIL]"
        if not exists:
            total_issues += 1
        print(f"    {status} function {func_name}(): {'存在' if exists else '不存在'}")
    print()

    print("  4b. 练习类型渲染函数检查")
    print()
    exercise_types = {
        'fill_blank (fill)': 'renderFillExercise',
        'char_to_pinyin': 'renderCharToPinyinExercise',
        'pinyin_to_char': 'renderPinyinToCharExercise',
        'read': 'renderReadExercise',
    }
    for type_name, render_func in exercise_types.items():
        exists = func_results.get(render_func, False)
        status = "[PASS]" if exists else "[FAIL]"
        if not exists:
            total_issues += 1
        print(f"    {status} 练习类型 '{type_name}' -> {render_func}(): {'存在' if exists else '不存在'}")
    print()

    print("  4c. 通用答案验证函数检查")
    print()
    if func_results.get('selectQuizOption', False):
        print("    [PASS] selectQuizOption() 函数存在")
    else:
        print("    [FAIL] selectQuizOption() 函数不存在")
        total_issues += 1
    if func_results.get('selectFillOption', False):
        print("    [PASS] selectFillOption() 函数存在")
    else:
        print("    [FAIL] selectFillOption() 函数不存在")
        total_issues += 1
    print()

    # ============================================================
    # 测试 5: 模板覆盖率测试
    # ============================================================
    print("-" * 70)
    print("测试 5: 模板覆盖率测试")
    print("-" * 70)
    print()

    all_chars_set = set(all_unique_chars.keys())
    total_chars = len(all_chars_set)
    chars_with_templates = set(templates.keys())
    template_count = len(chars_with_templates)
    coverage = (template_count / total_chars * 100) if total_chars > 0 else 0

    print(f"  5a. 基本统计")
    print()
    print(f"    BOOK_DATA 中唯一字符总数: {total_chars}")
    print(f"    有专属模板的字符数: {template_count}")
    print(f"    通用模板数量: {generic_count}")
    print(f"    模板覆盖率: {coverage:.1f}%")
    print(f"    未覆盖字符数: {total_chars - template_count}")

    if coverage >= 80:
        print(f"    [PASS] 覆盖率 {coverage:.1f}% >= 80%")
    elif coverage >= 50:
        print(f"    [WARN] 覆盖率 {coverage:.1f}% 在 50%-80% 之间")
    else:
        print(f"    [FAIL] 覆盖率 {coverage:.1f}% < 50%")
        total_issues += 1
    print()

    uncovered_chars = sorted(all_chars_set - chars_with_templates)
    if uncovered_chars:
        print(f"  5b. 未覆盖的字符 ({len(uncovered_chars)} 个)")
        print()
        line = "    "
        for i, ch in enumerate(uncovered_chars):
            line += f"'{ch}' "
            if (i + 1) % 20 == 0:
                print(line)
                line = "    "
        if line.strip():
            print(line)
    else:
        print("  5b. 所有字符都有专属模板")
    print()

    extra_template_chars = sorted(chars_with_templates - all_chars_set)
    if extra_template_chars:
        print(f"  5c. 有模板但不在 BOOK_DATA 中的字符 ({len(extra_template_chars)} 个)")
        print()
        for ch in extra_template_chars:
            print(f"    '{ch}'")
    else:
        print("  5c. 所有模板字符都在 BOOK_DATA 中")
    print()

    print("  5d. 模板数量分布")
    print()
    dist = {}
    for ch, tl in templates.items():
        c = len(tl)
        dist[c] = dist.get(c, 0) + 1
    for c in sorted(dist.keys()):
        print(f"    {c} 个模板: {dist[c]} 个字符")
    print()

    # ============================================================
    # 总结
    # ============================================================
    print("=" * 70)
    print("  测试总结")
    print("=" * 70)
    print()
    print(f"  总发现问题数: {total_issues}")
    print(f"  专属模板字符数: {template_count}/{total_chars} (覆盖率 {coverage:.1f}%)")
    print(f"  通用模板数: {generic_count}")
    print(f"  fixWords 覆盖字符数: {len(commonWords)}")
    print()
    if total_issues == 0:
        print("  [ALL PASS] 所有测试通过！")
    else:
        print(f"  [ISSUES FOUND] 发现 {total_issues} 个问题，请查看上方详细报告")
    print()
    print("=" * 70)

if __name__ == '__main__':
    main()
