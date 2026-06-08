from memory import add_message, print_history
from react_loop import run_react_agent
from roco_tool import fetch_merchant_all as _fetch_all


def fetch_merchant():
    """获取所有轮次的完整旅行商人商品信息（含当前和过往）。"""
    return _fetch_all()


def main():
    print("[洛可可王国旅行商人 Agent 已启动]")
    while True:
        try:
            user_input = input("\n你：")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in ("exit", "quit", "退出"):
            break
        if not user_input.strip():
            continue
        add_message("User", user_input)
        response = run_react_agent(user_input, tools=[fetch_merchant])
        print(f"Agent：{response}")
        add_message("Agent", response)
    print_history()


if __name__ == "__main__":
    main()
