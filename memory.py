history = []

def add_message(role, content):
    history.append({"role": role, "content": content})

def get_history():
    return list(history)

def print_history():
    for entry in history:
        print(f"[{entry['role']}] {entry['content']}")


