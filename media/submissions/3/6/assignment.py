# Data Structures Implementation
class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None
    
    def is_empty(self):
        return len(self.items) == 0

# Test the stack
stack = Stack()
stack.push(1)
stack.push(2)
print(stack.pop())  # Output: 2
