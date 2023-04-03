import functools
from pathlib import Path
import re


@functools.cache
def load() -> dict[str, str]:
    """ a hacky, unoptimized parser for normalize_env.rs :) """
    path = Path(__file__).parent/'normalize_env.rs'
    result: dict[str, str] = {}
    with open(path) as fp:
        keys: list[str] = []
        for line in fp:
            line = line.strip()
            if line.startswith('//'):   # comment
                continue
            while line:
                if line.startswith('|'):
                    line = line[1:].strip()
                elif line.startswith('"'):
                    i = line.index('"', 1)
                    keys.append(line[1:i])
                    line = line[i+1:].strip()
                elif line.startswith('=>'):
                    line = line[2:].strip()
                elif line.startswith('AmsEnv::'):
                    match = re.match(r'^AmsEnv::(?P<name>[a-zA-Z]+)\s*,', line)
                    assert match is not None
                    name = match.group('name')
                    line = line[match.endpos:]

                    # add keys
                    for key in keys:
                        result[key] = name
                    keys = []
                elif line.startswith('_'):
                    line = line[1:].strip()
                else:
                    raise Exception(f'String {line} not processable')

    return result


if __name__ == '__main__':
    print(load())
