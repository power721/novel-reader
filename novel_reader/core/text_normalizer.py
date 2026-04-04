"""
文本规范化模块 - 小说 TTS 文本预处理

提供小说文本的规范化处理，包括：
- 标点符号转换
- 数字格式化
- 英文单词保护
- 专有名词/缩写替换
- 韵律提示
"""
import re

# ==================== 常量 ====================

AUDIO_DIR = None  # 延迟初始化，由 tts_engine 设置

# ==================== 正则 ====================

EN_WORD_RE = re.compile(r"\b[A-Za-z]{2,}\b")

QUOTE_RE = re.compile(r'[「](.+?)[」]')

# 任意 ASCII 字母（最低判定）
ASCII_LETTER_RE = re.compile(r'[A-Za-z]')

# 英文块（哪怕一个字母）
EN_BLOCK_RE = re.compile(r'[A-Za-z][A-Za-z0-9\s.,:;!?\'"()+\-_/]*')

# ==================== 规范化函数 ====================


def normalize_for_novel_tts(text: str) -> str:
    text = basic_clean(text)
    text = normalize_numbers(text)
    text = normalize_punctuation(text)
    text = protect_english_words(text)
    text = normalize_levels(text)
    text = normalize_with_dict(text)
    text = prosody_hint(text)
    text = restore_english_words(text)
    return text


def basic_clean(text: str) -> str:
    text = text.replace('\u3000', ' ')
    text = text.replace('…', '……')
    text = text.replace('"', '「').replace('"', '」')
    text = text.replace(''', '『').replace(''', '』')
    return text.strip()


def normalize_punctuation(text: str) -> str:
    # 连续标点压缩
    text = re.sub(r'[！？]{2,}', '！', text)
    text = re.sub(r'[。]{2,}', '。', text)
    text = re.sub(r'={3,}', ' ', text)
    # 英文标点 → 中文
    text = text.replace(',', '，').replace('.', '。')
    return text


LEVEL_MAP = {
    "A": "甲",
    "B": "乙",
    "C": "丙",
    "D": "丁",
    "E": "戊",
}


def protect_english_words(text: str) -> str:
    """
    保护完整英文单词，防止被 OS / A / B 等子规则拆解
    """
    def repl(m):
        return f"⟪{m.group(0)}⟫"

    return EN_WORD_RE.sub(repl, text)


def restore_english_words(text: str) -> str:
    return re.sub(r"⟪([A-Za-z]+)⟫", r"\1", text)


def normalize_levels(text: str) -> str:
    def repl(m):
        return LEVEL_MAP[m.group(1)] + m.group(2)

    return re.sub(r'([ABCDE])([级等类档区组阶号])', repl, text)


ACRONYM_MAP = {
    "CPU": "西皮尤",
    "GPU": "吉皮尤",
    "NPU": "恩皮尤",
    "RAM": "内存",
    "ROM": "只读存储",
    "IO": "输入输出",
    "I/O": "输入输出",
    "AI": "诶艾",
    "ML": "机器学习",
    "DL": "深度学习",
    "UUID": "通用唯一识别码",
}
NETWORK_MAP = {
    "IP": "艾屁",
    "TCP": "提西皮",
    "UDP": "优迪皮",
    "HTTP": "艾尺提提屁",
    "HTTPS": "艾尺提提屁艾丝",
    "URL": "优艾儿艾",
    "DNS": "迪恩艾丝",
    "LAN": "局域网",
    "WAN": "广域网",
}
SOFTWARE_MAP = {
    "API": "诶皮艾",
    "SDK": "艾丝迪开",
    "IDE": "集成开发环境",
    "CLI": "命令行界面",
    "GUI": "图形界面",
    "OS": "操作系统",
    "DB": "数据库",
    "SQL": "数据库语言",
}
ZONE_MAP = {
    "A区": "甲区",
    "B区": "乙区",
    "C区": "丙区",

    "A组": "甲组",
    "B组": "乙组",
    "C组": "丙组",

    "A号": "甲号",
    "B号": "乙号",
}
MIXED_MAP = {
    "Dockerfile": "Docker 文件",
    "Web服务器": "网络服务器",
    "Web端": "网页端",
    "App端": "应用端",
    "Server端": "服务器端",
}
UNIT_MAP = {
    "GB": "吉字节",
    "MB": "兆字节",
    "KB": "千字节",
    "GHz": "吉赫兹",
    "MHz": "兆赫兹",
}

NORMALIZE_DICT = {}
NORMALIZE_DICT.update(ACRONYM_MAP)
NORMALIZE_DICT.update(NETWORK_MAP)
NORMALIZE_DICT.update(SOFTWARE_MAP)
NORMALIZE_DICT.update(ZONE_MAP)
NORMALIZE_DICT.update(MIXED_MAP)
NORMALIZE_DICT.update(UNIT_MAP)


def normalize_with_dict(text: str) -> str:
    # key 长度从大到小，避免 OS 抢在 OSS 前
    for k in sorted(NORMALIZE_DICT, key=len, reverse=True):
        v = NORMALIZE_DICT[k]

        # 只匹配"完整词"的英文
        if k.isalpha() and k.isupper():
            pattern = rf"\b{k}\b"
        else:
            # 非纯英文 key（比如符号）才允许直接替
            pattern = re.escape(k)

        text = re.sub(pattern, v, text)

    return text


def normalize_numbers(text: str) -> str:
    # 处理小数：0.05 → 0点05
    text = re.sub(r'(\d+)\.(\d+)', r'\1点\2', text)
    text = re.sub(r'(\d+)岁', r'\1 岁', text)
    text = re.sub(r'(\d+)年', r'\1 年', text)
    text = re.sub(r'(\d+)km', r'\1 公里', text)
    text = re.sub(r'(\d+)%', r'百分之\1', text)
    return text


def prosody_hint(text: str) -> str:
    text = text.replace('，但是', '，不过')
    text = text.replace('。但是', '。不过')
    return text
