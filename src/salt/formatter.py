"""输出格式化模块 - 使用 rich 美化输出"""

import json
from typing import Any, Dict

from rich.console import Console
from rich.json import JSON
from rich.table import Table
from rich.panel import Panel


class OutputFormatter:
    """输出格式化器"""

    def __init__(self, raw: bool = False):
        self.raw = raw
        self.console = Console()

    def print_json(self, data: Any):
        """打印 JSON 数据"""
        if self.raw:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            self.console.print(JSON(json_str))

    def print_dict(self, data: Dict):
        """打印字典数据（表格形式）"""
        if self.raw:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")

            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = str(value)
                table.add_row(key, value_str)

            self.console.print(table)

    def print_result(self, result: Dict):
        """打印 Salt API 返回结果"""
        if self.raw:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        # 提取 return 字段
        if "return" in result and isinstance(result["return"], list):
            for item in result["return"]:
                if isinstance(item, dict):
                    # 为每个 minion 创建一个面板
                    for minion, data in item.items():
                        self._print_minion_result(minion, data)
                else:
                    self.console.print(item)
        else:
            self.print_json(result)

    def _print_minion_result(self, minion: str, data: Any):
        """打印单个 minion 的结果"""
        if isinstance(data, dict):
            # 如果是字典，使用表格展示
            table = Table(show_header=True, header_style="bold cyan", title=f"[bold]{minion}[/bold]")
            table.add_column("Key", style="yellow")
            table.add_column("Value", style="green")

            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, ensure_ascii=False, indent=2)
                else:
                    value_str = str(value)
                table.add_row(key, value_str)

            self.console.print(table)
        elif isinstance(data, bool):
            # 对于 ping 等返回布尔值的命令
            status = "[green]✓ True[/green]" if data else "[red]✗ False[/red]"
            self.console.print(f"[bold]{minion}[/bold]: {status}")
        else:
            # 其他类型直接打印
            self.console.print(Panel(str(data), title=minion, border_style="cyan"))

    def print_error(self, message: str):
        """打印错误信息"""
        if self.raw:
            print(f"Error: {message}")
        else:
            self.console.print(f"[bold red]错误:[/bold red] {message}")

    def print_success(self, message: str):
        """打印成功信息"""
        if self.raw:
            print(message)
        else:
            self.console.print(f"[bold green]✓[/bold green] {message}")

    def print_clusters(self, clusters: list):
        """打印环境列表"""
        if self.raw:
            data = [c.to_dict() for c in clusters]
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            table = Table(show_header=True, header_style="bold magenta", title="[bold]Salt 环境列表[/bold]")
            table.add_column("名称", style="cyan", no_wrap=True)
            table.add_column("描述", style="yellow")
            table.add_column("API 地址", style="green")
            table.add_column("认证方式", style="blue")

            for cluster in clusters:
                table.add_row(
                    cluster.name,
                    cluster.description,
                    cluster.base_url,
                    cluster.eauth,
                )

            self.console.print(table)
