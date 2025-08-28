import toml
import sys

file_path = sys.argv[1] if len(sys.argv) > 1 else 'pyproject.toml'

try:
    with open(file_path, 'r') as f:
        content = f.read()
    parsed = toml.loads(content)
    print(f'✅ {file_path} is correctly formatted.')
    print(f'Found sections: {list(parsed.keys())}')
except FileNotFoundError:
    print(f'❌ File {file_path} not found.')
except toml.TomlDecodeError as e:
    print(f'❌ TOML syntax error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
