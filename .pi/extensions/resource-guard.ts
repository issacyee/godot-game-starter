// 仅拦截 Pi 的直接 write/edit；不是 Shell 或任意脚本沙箱。
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export function protectedResource(toolName: string, input: Record<string, unknown>): boolean {
  const leaf = toolName.split(/[.:]/).pop();
  return (leaf === "write" || leaf === "edit") &&
    typeof input.path === "string" && /\.(tscn|tres)$/i.test(input.path);
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event) => {
    if (protectedResource(event.toolName, event.input)) {
      return { block: true, reason: "场景／资源请用 Godot AI 结构化修改、保存并重载验证；直接文本写入被拦截。" };
    }
  });
}
