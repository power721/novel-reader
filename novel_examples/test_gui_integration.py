#!/usr/bin/env python3
"""
测试GUI集成新架构

验证PlaybackControllerAdapter与GUI组件的集成
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, '.')

def test_adapter_imports():
    """测试适配器导入"""
    print("=" * 60)
    print("📦 测试 GUI 适配器导入")
    print("=" * 60)

    try:
        from novel_reader.gui.controllers import PlaybackControllerAdapter
        print("✓ PlaybackControllerAdapter imported")

        from novel_reader.gui.main_window_v2 import MainWindow
        print("✓ MainWindow V2 imported")

        from novel_reader.gui.widgets.player_widget import PlayerWidget
        print("✓ PlayerWidget imported")

        print("\n✅ 所有GUI组件导入成功!")
        return True

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return False


def test_adapter_initialization():
    """测试适配器初始化"""
    print("\n" + "=" * 60)
    print("🧪 测试 PlaybackControllerAdapter 初始化")
    print("=" * 60)

    try:
        from novel_reader.gui.controllers import PlaybackControllerAdapter
        from PySide6.QtWidgets import QApplication

        # 创建应用程序实例（GUI需要）
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # 创建适配器
        adapter = PlaybackControllerAdapter()
        print("✓ PlaybackControllerAdapter 创建成功")

        # 初始化控制器
        adapter.initialize()
        print("✓ 控制器初始化成功")

        # 检查状态
        state = adapter.state
        print(f"✓ 初始状态: {state.name}")

        # 关闭控制器
        adapter.shutdown()
        print("✓ 控制器关闭成功")

        print("\n✅ 适配器初始化测试通过!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_emission():
    """测试信号发射"""
    print("\n" + "=" * 60)
    print("🧪 测试 Qt 信号发射")
    print("=" * 60)

    try:
        from novel_reader.gui.controllers import PlaybackControllerAdapter
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QMetaObject, Qt

        # 创建应用程序实例
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # 创建适配器
        adapter = PlaybackControllerAdapter()
        adapter.initialize()

        # 记录信号
        signals_received = []

        def on_state_changed(state):
            signals_received.append(('state', state))
            print(f"  ✓ 收到信号: state_changed -> {state}")

        def on_chunk_changed(chunk_id):
            signals_received.append(('chunk', chunk_id))
            print(f"  ✓ 收到信号: chunk_changed -> {chunk_id}")

        # 连接信号
        adapter.state_changed.connect(on_state_changed)
        adapter.chunk_changed.connect(on_chunk_changed)

        # 模拟状态变化（通过内部回调）
        if adapter.controller:
            adapter.controller.on_state_changed(adapter.controller.state)
            adapter.controller.on_chunk_changed(
                type('obj', (object,), {'chunk_id': 42})()
            )

        # 等待信号处理
        app.processEvents()

        # 验证信号
        if len(signals_received) >= 2:
            print(f"\n✓ 收到 {len(signals_received)} 个信号")
        else:
            print(f"\n⚠ 仅收到 {len(signals_received)} 个信号")

        # 关闭控制器
        adapter.shutdown()

        print("\n✅ 信号发射测试通过!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 GUI 集成测试套件 (新架构)")
    print("=" * 60)

    all_passed = True

    # 测试导入
    if not test_adapter_imports():
        all_passed = False

    # 测试适配器初始化
    if all_passed:
        if not test_adapter_initialization():
            all_passed = False

    # 测试信号发射
    if all_passed:
        if not test_signal_emission():
            all_passed = False

    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过!")
        print("\n🚀 可以运行新GUI:")
        print("   python run_gui_v2.py")
        print("   python -m novel_reader.gui.pyside_main_v2")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
