```
novel-reader/
├── .git/
├── .github/
│   └── workflows/
├── novel_reader/                 # 主程序包
│   ├── __init__.py              # 包初始化
│   ├── __main__.py              # python -m novel_reader 入口
│   ├── main.py                  # 程序主入口
│   ├── cli.py                   # CLI 命令行接口
│   │
│   ├── ui/                      # TUI 界面层
│   │   ├── __init__.py
│   │   ├── app.py               # Textual App 主类
│   │   ├── screens/             # 各个界面屏幕
│   │   │   ├── __init__.py
│   │   │   ├── home.py          # 主屏幕（书籍列表）
│   │   │   ├── book.py          # 书籍详情屏幕
│   │   │   ├── player.py        # 播放器屏幕
│   │   │   ├── bookmarks.py     # 书签列表屏幕
│   │   │   └── settings.py      # 设置屏幕
│   │   └── widgets/             # 自定义组件
│   │       ├── __init__.py
│   │       ├── book_card.py     # 书籍卡片
│   │       ├── chapter_list.py  # 章节列表
│   │       ├── progress_bar.py  # 进度条
│   │       └── player_controls.py # 播放控制组件
│   │
│   ├── core/                    # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── library.py           # 图书馆管理
│   │   ├── book.py              # 书籍管理
│   │   ├── chapter.py           # 章节管理
│   │   ├── tts.py               # TTS 转换引擎
│   │   ├── player.py            # 音频播放器（封装 mpv）
│   │   └── bookmark.py          # 书签管理
│   │
│   ├── models/                  # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py          # 数据库连接和初始化
│   │   ├── schemas.py           # 数据库 Schema 定义
│   │   └── entities.py          # 业务实体类
│   │
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       ├── config.py            # 配置管理
│       ├── path.py              # 路径工具
│       ├── time.py              # 时间工具
│       └── subprocess.py        # 子进程管理（piper/mpv）
│
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置
│   ├── test_core/               # 核心逻辑测试
│   ├── test_ui/                 # UI 测试
│   └── test_models/             # 模型测试
│
├── docs/                        # 文档（可选）
│   └── architecture.md          # 架构设计文档
│
├── .gitignore                   # Git 忽略文件
├── LICENSE                      # 许可证
├── README.md                    # 项目说明
├── requirements.txt             # Python 依赖
├── setup.py                     # 包安装配置（可选）
└── pyproject.toml               # 现代 Python 项目配置（可选）

用户数据目录（运行时创建）：
├── ~/.config/novel-reader/      # 配置文件
│   └── config.json
├── ~/.local/share/novel-reader/ # 数据文件
│   ├── library.db               # SQLite 数据库
│   ├── audio/                   # 生成的音频文件
│   │   └── <book_id>/
│   │       └── <chapter_id>.wav
│   └── models/                  # TTS 模型
│       └── <model_name>/
└── ~/.cache/novel-reader/       # 缓存
    └── logs/                    # 日志文件
```
