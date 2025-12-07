import unittest
import sys
import os

# Add the 'src' directory to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.static_analyzer import analyze_file_changes

class TestStaticAnalyzer(unittest.TestCase):

    def test_analyze_file_changes(self):
        # 1. Define a sample original file content
        # This represents the NEW state of the file, after the patch is applied.
        new_file_content = """
                def hello_world():
                    print("Hello, world!")

                def goodbye(name):
                    print(f"Goodbye, {name}!")
                    print("See you later!")

                class MyClass:
                    def method(self):
                        return 1
            """

        # 2. Define a sample patch that modifies the 'goodbye' function
        # This patch corresponds to the change in new_file_content
        patch_text = """
            @@ -4,3 +4,4 @@
            
            def goodbye(name):
                print(f"Goodbye, {name}!")
            +    print("See you later!")
        """

        # 3. Call the function you want to test
        affected_nodes = analyze_file_changes(new_file_content, patch_text)

        # 4. Assert the results are what you expect
        # We expect it to identify that 'goodbye' was changed.
        self.assertIn("goodbye", affected_nodes)

        # We expect it NOT to identify 'hello_world' as changed.
        self.assertNotIn("hello_world", affected_nodes)

        # We expect the full source code of the 'goodbye' function to be returned.
        expected_source = "def goodbye(name):\n    print(f'Goodbye, {name}!')\n    print('See you later!')"

        self.assertEqual(affected_nodes["goodbye"].strip(), expected_source.strip())


if __name__ == '__main__':
    unittest.main()
