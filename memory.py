class MemoryStore:
    def __init__(self):
        self.store_dict = {}

    def store(self, user_id, text, entry_type="chat", query=None):
        if user_id not in self.store_dict:
            self.store_dict[user_id] = []

        entry = {"type": entry_type, "text": text}
        if query:
            entry["query"] = query

        self.store_dict[user_id].append(entry)

        if len(self.store_dict[user_id]) > 3:
            self.store_dict[user_id].pop(0)

    def get_last(self, user_id):
        if user_id in self.store_dict and self.store_dict[user_id]:
            return self.store_dict[user_id][-1]
        return None

    def get_history(self, user_id):
        return list(self.store_dict.get(user_id, []))

    def get_last_n(self, user_id, n=3):
        history = self.store_dict.get(user_id, [])
        return history[-n:]
