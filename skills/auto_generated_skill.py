# PLAN
# Goal: Calculate the 10th Fibonacci number and return it in a sentence.
# Logic Steps:
# 1. Define the index (n=10) for the Fibonacci sequence.
# 2. Implement an iterative function to calculate the Fibonacci number at index n.
# 3. The Fibonacci sequence used starts with F(0)=0 and F(1)=1.
# 4. Perform the calculation to find that F(10) is 55.
# 5. Format the result into a human-readable sentence.
# 6. Return the sentence through the execute method.
# Required Libraries: None.

class BaseSkill:
    def execute(self, **kwargs):
        """Method to be overridden by subclasses."""
        pass

class GeneratedSkill(BaseSkill):
    def _calculate_fibonacci(self, n):
        """Calculates the n-th Fibonacci number iteratively."""
        if n <= 0:
            return 0
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

    def execute(self, **kwargs):
        """Executes the skill logic to find the 10th Fibonacci number."""
        index = 10
        fib_number = self._calculate_fibonacci(index)
        return f"The 10th Fibonacci number is {fib_number}."
