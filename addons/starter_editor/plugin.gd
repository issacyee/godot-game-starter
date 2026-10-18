@tool
extends EditorPlugin


func _enter_tree() -> void:
	var settings: EditorSettings = EditorInterface.get_editor_settings()
	var domains: PackedStringArray = str(settings.get_setting("godot_ai/excluded_domains") if settings.has_setting("godot_ai/excluded_domains") else "").split(",", false)
	if not domains.has("testing"):
		domains.append("testing")
	settings.set_setting("godot_ai/excluded_domains", ",".join(domains))
	settings.set_setting("godot_ai/telemetry_enabled", false)
	var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://tools/ai-config.json"))
	if raw is Dictionary:
		for domain: String in raw.get("exclude_domains", []):
			if not domains.has(domain):
				domains.append(domain)
		settings.set_setting("godot_ai/excluded_domains", ",".join(domains))
		settings.set_setting("godot_ai/v4_endpoint_ports", {"http_port": int(raw.http_port), "ws_port": int(raw.ws_port)})
