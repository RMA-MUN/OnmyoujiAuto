import yaml

class ConfigReader:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_config(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                print("已成功读取配置文件。")
                return yaml.safe_load(f)
        except Exception as e:
            error_msg = f"读取配置文件 {self.file_path} 时出现异常: {e}"
            print(error_msg)
            return None