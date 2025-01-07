from pathlib import Path

import mod_resource
import mod_something

if __name__ == '__main__':
    print(f'Hello, world! -> something returns: {mod_something.something()}')

    res_path = Path(mod_resource.__file__).parent / 'resource.txt'
    text = res_path.read_text(encoding='utf-8')
    print(f'From mod_resource:resource.txt -> {text}')
