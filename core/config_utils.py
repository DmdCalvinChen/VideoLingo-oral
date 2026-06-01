from ruamel.yaml import YAML
from typing import Any
import os, sys
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_PATH = 'config.yaml'
config_lock = threading.Lock()

yaml = YAML()
yaml.preserve_quotes = True

def load_key(key: str) -> Any:
    with config_lock:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = yaml.load(file)
            
        secret_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.secret')
        if os.path.exists(secret_path):
            with open(secret_path, 'r', encoding='utf-8') as f:
                secret_data = yaml.load(f)
                if secret_data:
                    for k, v in secret_data.items():
                        if k in data and isinstance(data[k], dict) and isinstance(v, dict):
                            data[k].update(v)
                        else:
                            data[k] = v

    keys = key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            raise KeyError(f"Key '{k}' not found in configuration")
    return value

def update_key(key: str, new_value: Any) -> bool:
    with config_lock:
        keys = key.split('.')
        secret_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.secret')
        
        # Check if key exists in .secret
        updated_in_secret = False
        if os.path.exists(secret_path):
            with open(secret_path, 'r', encoding='utf-8') as file:
                secret_data = yaml.load(file)
            
            if secret_data:
                current_secret = secret_data
                for k in keys[:-1]:
                    if isinstance(current_secret, dict) and k in current_secret:
                        current_secret = current_secret[k]
                    else:
                        break
                else:
                    if isinstance(current_secret, dict) and keys[-1] in current_secret:
                        current_secret[keys[-1]] = new_value
                        with open(secret_path, 'w', encoding='utf-8') as file:
                            yaml.dump(secret_data, file)
                        updated_in_secret = True

        if updated_in_secret:
            return True

        # Fallback to config.yaml if not updated in .secret
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = yaml.load(file)

        current = data
        for k in keys[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False

        if isinstance(current, dict) and keys[-1] in current:
            current[keys[-1]] = new_value
            with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
                yaml.dump(data, file)
            return True
        else:
            raise KeyError(f"Key '{keys[-1]}' not found in configuration")
        
# basic utils
def get_joiner(language):
    if language in load_key('language_split_with_space'):
        return " "
    elif language in load_key('language_split_without_space'):
        return ""
    else:
        raise ValueError(f"Unsupported language code: {language}")

if __name__ == "__main__":
    print(load_key('language_split_with_space'))
