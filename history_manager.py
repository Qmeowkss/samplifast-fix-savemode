class HistoryManager:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def save_state(self, state):
        import copy
        self.undo_stack.append(copy.deepcopy(state))
        self.redo_stack.clear()

    def undo(self, current_state):
        import copy
        if not self.undo_stack:
            return current_state
        self.redo_stack.append(copy.deepcopy(current_state))
        return self.undo_stack.pop()

    def redo(self, current_state):
        import copy
        if not self.redo_stack:
            return current_state
        self.undo_stack.append(copy.deepcopy(current_state))
        return self.redo_stack.pop()
