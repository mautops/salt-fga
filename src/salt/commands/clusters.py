"""clusters 命令 - 查看和管理环境配置"""

from ..config import ConfigManager
from ..formatter import OutputFormatter


class ClustersCommand:
    """环境管理命令"""

    def __init__(self, config_manager: ConfigManager, formatter: OutputFormatter):
        self.config_manager = config_manager
        self.formatter = formatter

    def list(self):
        """列出所有环境"""
        try:
            clusters = self.config_manager.list_clusters()
            self.formatter.print_clusters(clusters)
        except Exception as e:
            self.formatter.print_error(str(e))
            raise

    def __call__(self):
        """默认行为：列出所有环境"""
        self.list()
