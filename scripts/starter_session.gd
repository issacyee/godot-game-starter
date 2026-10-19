@abstract class_name StarterSession
extends Node
## 两个示例共用的生命周期接线；空间观测和物理由具体场景实现。

const Rules = preload("res://scripts/round_rules.gd")
const Journal = preload("res://scripts/diagnostic_journal.gd")

@export var tuning: StarterTuning

@onready var status: Label = $Interface/Panel/Rows/Status
@onready var start_button: Button = $Interface/Panel/Rows/Start
@onready var pause_button: Button = $Interface/Panel/Rows/Pause
@onready var restart_button: Button = $Interface/Panel/Rows/Restart

var rules: RoundRules
var _values: Dictionary
var _journal: DiagnosticJournal
var _presentation: StarterUI
var _source: String
var _probe: ProductProbe
var _build: Dictionary = {"channel": "editor", "source_hash": "unbuilt"}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.has("--preset"):
		var index: int = args.find("--preset")
		if not OS.is_debug_build() or index + 1 >= args.size() or args[index + 1] != "slow":
			push_error("PRESET_INVALID: 仅 dev 支持显式 slow 预设")
			get_tree().quit(2)
			return
		tuning = load("res://tuning/slow_2d.tres" if route() == "2d" else "res://tuning/slow.tres") as StarterTuning
	_source = tuning.resource_path if tuning != null else "missing"
	if FileAccess.file_exists("res://build_identity.json"):
		_build = JSON.parse_string(FileAccess.get_file_as_string("res://build_identity.json"))
	if tuning == null or not tuning.validate_for(route()).is_empty():
		push_error("TUNING_INVALID: 缺少、错配或无效的参数资源")
		get_tree().quit(2)
		return
	_values = tuning.effective_values()
	_journal = Journal.new(int(_values.diagnostic_capacity))
	rules = Rules.new(float(_values.interaction_reach))
	_connect_world()
	var panel: PanelContainer = $Interface/Panel
	if panel.theme != null:
		panel.theme = panel.theme.duplicate() as Theme
		panel.theme.default_font_size = int(_values.text_size)
	_probe = ProductProbe.new(self)
	_presentation.present(rules.view())


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_F8 and _probe != null:
		_probe.capture_requested = true


func _process(delta: float) -> void:
	if rules != null:
		if Input.is_action_just_pressed("ui_accept"):
			request(&"start" if not rules.view().running else &"interact")
		if Input.is_action_just_pressed("ui_cancel"):
			request(&"continue" if rules.view().paused else &"pause")
		if Input.is_action_just_pressed("restart"):
			request(&"restart")
	if _probe != null:
		_probe.advance(delta)


func _physics_process(delta: float) -> void:
	if rules == null:
		return
	var active: bool = rules.view().running and not rules.view().paused
	_move(Input.get_vector("move_left", "move_right", "move_forward", "move_back", float(_values.direction_deadzone)) if active else Vector2.ZERO)
	if active:
		rules.advance(delta)


func request(action: StringName) -> int:
	var result: int = Rules.Result.INVALID
	match action:
		&"start", &"restart":
			get_tree().paused = false
			_reset_player()
			rules.start()
			result = Rules.Result.ACCEPTED
		&"pause", &"continue":
			result = rules.set_paused(action == &"pause")
			if result == Rules.Result.ACCEPTED:
				_move(Vector2.ZERO)
				get_tree().paused = action == &"pause"
		&"interact":
			result = rules.interact(_interaction_distance())
	_journal.record(action, result)
	_presentation.present(rules.view())
	return result


func diagnostic_snapshot() -> Dictionary:
	return {"schema": 2, "route": route(), "position_space": "world_local",
		"distance_unit": "px" if route() == "2d" else "m",
		"state": rules.view(), "parameters": _values.duplicate(true),
		"parameter_source": _source, "parameter_hash": JSON.stringify(_values, "", true).sha256_text(),
		"build": _build.duplicate(true), "journal": _journal.snapshot(), "position": _position_components()}


func _on_start_pressed() -> void:
	request(&"start")


func _on_pause_pressed() -> void:
	request(&"continue" if rules.view().paused else &"pause")


func _on_restart_pressed() -> void:
	request(&"restart")


func _exit_tree() -> void:
	if is_inside_tree():
		get_tree().paused = false


@abstract func route() -> String

@abstract func _connect_world() -> void

@abstract func _move(direction: Vector2) -> void

@abstract func _reset_player() -> void

@abstract func _interaction_distance() -> float

@abstract func _position_components() -> Array

@abstract func capture_points() -> Dictionary
