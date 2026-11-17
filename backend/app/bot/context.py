from __future__ import annotations

from collections import OrderedDict, deque

ChatMessage = dict[str, str]


class ConversationStore:
    """进程内的短期对话历史，按会话键保存最近若干轮。

    机器人是单进程运行；重启后历史丢失是可接受的，持久化留到后续阶段。
    """

    def __init__(self, max_conversations: int = 500) -> None:
        self._items: OrderedDict[str, deque[ChatMessage]] = OrderedDict()
        self._max_conversations = max_conversations

    def history(self, key: str) -> list[ChatMessage]:
        bucket = self._items.get(key)
        if bucket is None:
            return []
        self._items.move_to_end(key)
        return list(bucket)

    def append(
        self,
        key: str,
        user_message: str,
        assistant_message: str,
        max_turns: int,
    ) -> None:
        if max_turns <= 0:
            return
        existing = list(self._items.get(key, ()))
        bucket: deque[ChatMessage] = deque(existing, maxlen=max_turns * 2)
        bucket.extend(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
            ]
        )
        self._items[key] = bucket
        self._items.move_to_end(key)
        while len(self._items) > self._max_conversations:
            self._items.popitem(last=False)

    def clear(self) -> None:
        self._items.clear()


STORE = ConversationStore()
