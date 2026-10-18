extends GdUnitTestSuite

const Main = preload("res://scripts/main.gd")
const Presentation = preload("res://scripts/starter_presentation.gd")


func after_test() -> void:
	Input.action_release("move_right")
	for action: StringName in [&"ui_accept", &"ui_cancel", &"restart"]:
		Input.action_release(action)
	get_tree().paused = false


func test_saved_scene_reloads_with_resources_owners_and_signals() -> void:
	var packed: PackedScene = ResourceLoader.load("res://scenes/main.tscn", "PackedScene", ResourceLoader.CACHE_MODE_IGNORE)
	assert_object(packed).is_not_null()
	var scene: Node = auto_free(packed.instantiate())
	assert_object(scene.get_node("World/Player").owner).is_same(scene)
	assert_object(scene.get_node("World/Player").get_script()).is_not_null()
	assert_object(scene.get_node("World/Player/Collider").shape).is_not_null()
	assert_object(scene.tuning).is_not_null()
	assert_int(scene.get_node("Interface/Panel/Rows/Start").get_signal_connection_list("pressed").size()).is_equal(1)
	# 保存后重新加载，不只观察编辑器内存。user:// 已由运行器重定向至一次性 profile。
	var saved := PackedScene.new()
	assert_int(saved.pack(scene)).is_equal(OK)
	assert_int(ResourceSaver.save(saved, "user://roundtrip.tscn")).is_equal(OK)
	var reloaded: PackedScene = ResourceLoader.load("user://roundtrip.tscn", "PackedScene", ResourceLoader.CACHE_MODE_IGNORE)
	var other: Node = auto_free(reloaded.instantiate())
	assert_object(other.get_node("World/Player").owner).is_same(other)
	assert_int(other.get_node("Interface/Panel/Rows/Restart").get_signal_connection_list("pressed").size()).is_equal(1)
	assert_float(other.tuning.move_speed).is_equal(4.0)


func test_scene_flow_physics_interaction_pause_and_restart() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://scenes/main.tscn")
	var scene: StarterMain = runner.scene() as StarterMain
	assert_bool(scene.rules.view().running).is_false()
	# 验证持久信号真正接线。
	scene.start_button.pressed.emit()
	assert_bool(scene.rules.view().running).is_true()
	assert_int(scene.request(&"interact")).is_equal(RoundRules.Result.OUT_OF_RANGE)
	Input.action_press("move_right")
	var steps: int = 0
	while scene.player.position.x < 1.6 and steps < 120:
		await get_tree().physics_frame
		steps += 1
	Input.action_release("move_right")
	await get_tree().physics_frame
	assert_float(scene.player.position.x).is_greater_equal(1.6)
	assert_int(scene.request(&"interact")).is_equal(RoundRules.Result.ACCEPTED)
	assert_bool(scene.target.visible).is_false()
	scene.request(&"pause")
	var position: Vector3 = scene.player.position
	var elapsed: float = scene.rules.view().elapsed
	Input.action_press("move_right")
	for _frame: int in range(5):
		await get_tree().physics_frame
	assert_vector(scene.player.position).is_equal(position)
	assert_float(scene.rules.view().elapsed).is_equal(elapsed)
	Input.action_release("move_right")
	scene.request(&"continue")
	await get_tree().physics_frame
	await get_tree().physics_frame
	assert_float(scene.rules.view().elapsed).is_greater(elapsed)
	for _index: int in range(3):
		scene.request(&"pause")
		scene.request(&"restart")
		assert_bool(get_tree().paused).is_false()
		assert_vector(scene.player.position).is_equal(Vector3(0.0, 0.5, 0.0))
		assert_bool(scene.rules.view().activated).is_false()
		assert_bool(scene.target.visible).is_true()
	assert_float(scene.tuning.move_speed).is_equal(4.0)


func test_semantic_input_polling_and_preset_are_used_by_scene() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://scenes/main.tscn")
	var scene: StarterMain = runner.scene() as StarterMain
	Input.action_press("ui_accept")
	await get_tree().process_frame
	await get_tree().process_frame
	Input.action_release("ui_accept")
	assert_bool(scene.rules.view().running).is_true()
	await get_tree().process_frame
	Input.action_press("ui_cancel")
	await get_tree().process_frame
	await get_tree().process_frame
	Input.action_release("ui_cancel")
	assert_bool(scene.rules.view().paused).is_true()
	var baseline: StarterTuning = load("res://tuning/baseline.tres") as StarterTuning
	var slow: StarterTuning = load("res://tuning/slow.tres") as StarterTuning
	assert_float(slow.move_speed).is_equal(2.0)
	assert_float(baseline.move_speed).is_equal(4.0)
	var panel: PanelContainer = scene.get_node("Interface/Panel") as PanelContainer
	assert_object(panel.theme.default_font).is_null()
	assert_object(scene.status.get_theme_font("font")).is_same(ThemeDB.fallback_font)
	assert_int(scene.status.get_theme_font_size("font_size")).is_equal(22)
	var saved_theme: Theme = ResourceLoader.load("res://assets/interface.tres", "Theme", ResourceLoader.CACHE_MODE_IGNORE) as Theme
	assert_object(saved_theme.default_font).is_null()


func test_experiment_resource_drives_actual_movement_without_mutating_baseline() -> void:
	var packed: PackedScene = load("res://scenes/main.tscn") as PackedScene
	var instance: StarterMain = auto_free(packed.instantiate()) as StarterMain
	instance.tuning = load("res://tuning/slow.tres") as StarterTuning
	var runner: GdUnitSceneRunner = scene_runner(instance)
	var scene: StarterMain = runner.scene() as StarterMain
	assert_float(scene.player.move_speed).is_equal(2.0)
	scene.request(&"start")
	Input.action_press("move_right")
	for _frame: int in range(12):
		await get_tree().physics_frame
	Input.action_release("move_right")
	assert_float(scene.player.position.x).is_between(0.30, 0.46)
	var baseline: StarterTuning = load("res://tuning/baseline.tres") as StarterTuning
	assert_float(baseline.move_speed).is_equal(4.0)


func test_physics_wall_prevents_escape() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://scenes/main.tscn")
	var scene: StarterMain = runner.scene() as StarterMain
	scene.request(&"start")
	Input.action_press("move_right")
	for _frame: int in range(120):
		await get_tree().physics_frame
	Input.action_release("move_right")
	assert_float(scene.player.position.x).is_between(5.4, 5.6)


func test_presentation_is_repeatable_without_gameplay_side_effects() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://scenes/main.tscn")
	var scene: StarterMain = runner.scene() as StarterMain
	# 表现模块只借用显示节点，不持有规则、玩家或协调器。
	var presenter: StarterPresentation = Presentation.new(
		scene.world, scene.target, scene.status,
		scene.start_button, scene.pause_button, scene.restart_button)
	var view: Dictionary = scene.rules.view()
	var before: Dictionary = scene.diagnostic_snapshot()
	presenter.present(view)
	presenter.present(view)
	assert_dict(view).is_equal(before.state)
	assert_dict(scene.diagnostic_snapshot()).is_equal(before)
	assert_bool(scene.world.visible).is_false()
	assert_bool(scene.start_button.visible).is_true()
	for action: StringName in [&"start", &"interact", &"pause", &"continue", &"restart"]:
		scene.request(action)
		view = scene.rules.view()
		before = scene.diagnostic_snapshot()
		var paused: bool = get_tree().paused
		var velocity: Vector3 = scene.player.velocity
		var direction: Vector2 = scene.player.direction
		presenter.present(view)
		var text: String = scene.status.text
		presenter.present(view)
		assert_bool(get_tree().paused).is_equal(paused)
		assert_vector(scene.player.velocity).is_equal(velocity)
		assert_vector(scene.player.direction).is_equal(direction)
		assert_str(scene.status.text).is_equal(text)
		assert_bool(scene.world.visible).is_equal(view.running)
		assert_bool(scene.target.visible).is_equal(not view.activated)
		assert_bool(scene.start_button.visible).is_equal(not view.running)
		assert_bool(scene.pause_button.visible).is_equal(view.running)
		assert_bool(scene.restart_button.visible).is_equal(view.running)
		assert_dict(view).is_equal(before.state)
		assert_dict(scene.diagnostic_snapshot()).is_equal(before)
	# 重建显示不依赖“上一次收到了激活事件”，也不恢复／改写物理位置。
	scene.player.position = Vector3(2.0, 0.5, 0.0)
	assert_int(scene.request(&"interact")).is_equal(RoundRules.Result.ACCEPTED)
	view = scene.rules.view()
	before = scene.diagnostic_snapshot()
	scene.target.visible = true
	presenter.present(view)
	assert_bool(scene.target.visible).is_false()
	assert_str(scene.status.text).is_equal("交互成功：目标已激活\nR 重开；Esc 暂停 / 继续")
	assert_dict(scene.diagnostic_snapshot()).is_equal(before)


func test_rule_view_is_detached_from_live_state() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://scenes/main.tscn")
	var scene: StarterMain = runner.scene() as StarterMain
	scene.request(&"start")
	var view: Dictionary = scene.rules.view()
	view.running = false
	view.paused = true
	view.activated = true
	view.elapsed = 999.0
	assert_dict(scene.rules.view()).is_equal({"running": true, "paused": false, "activated": false, "elapsed": 0.0})
