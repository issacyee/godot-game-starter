extends GdUnitTestSuite

const Presentation = preload("res://scripts/starter_presentation_2d.gd")


func after_test() -> void:
	for action: StringName in [&"move_right", &"move_left", &"move_forward", &"move_back", &"ui_accept", &"ui_cancel", &"restart"]:
		Input.action_release(action)
	get_tree().paused = false


func test_default_route_and_saved_scene_owners_resources_signals() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://starter-project.json"))
	var expected: String = "res://scenes/main.tscn" if config.route == "3d" else "res://scenes/main_2d.tscn"
	assert_str(ProjectSettings.get_setting("application/run/main_scene")).is_equal(expected)
	var packed: PackedScene = ResourceLoader.load("res://scenes/main_2d.tscn", "PackedScene", ResourceLoader.CACHE_MODE_IGNORE)
	assert_object(packed).is_not_null()
	var scene: StarterMain2D = auto_free(packed.instantiate()) as StarterMain2D
	assert_object(scene.get_node("World/Player").owner).is_same(scene)
	assert_object(scene.get_node("World/Player/Collider").shape).is_not_null()
	assert_int(scene.get_node("World/Player").motion_mode).is_equal(CharacterBody2D.MOTION_MODE_FLOATING)
	assert_str(scene.tuning.route).is_equal("2d")
	var saved := PackedScene.new()
	assert_int(saved.pack(scene)).is_equal(OK)
	assert_int(ResourceSaver.save(saved, "user://roundtrip-2d.tscn")).is_equal(OK)
	var reloaded: PackedScene = ResourceLoader.load("user://roundtrip-2d.tscn", "PackedScene", ResourceLoader.CACHE_MODE_IGNORE)
	var other: Node = auto_free(reloaded.instantiate())
	assert_object(other.get_node("World/Player").owner).is_same(other)
	for button: String in ["Start", "Pause", "Restart"]:
		assert_int(other.get_node("Interface/Panel/Rows/" + button).get_signal_connection_list("pressed").size()).is_equal(1)
	assert_float(other.tuning.move_speed).is_equal(200.0)


func test_input_flow_interaction_pause_continue_restart() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://scenes/main_2d.tscn")
	var scene: StarterMain2D = runner.scene() as StarterMain2D
	assert_bool(scene.rules.view().running).is_false()
	Input.action_press("ui_accept")
	await get_tree().process_frame
	await get_tree().process_frame
	Input.action_release("ui_accept")
	assert_bool(scene.rules.view().running).is_true()
	assert_int(scene.request(&"interact")).is_equal(RoundRules.Result.OUT_OF_RANGE)
	Input.action_press("move_right")
	var steps: int = 0
	while scene.player.position.x < 80.0 and steps < 120:
		await get_tree().physics_frame
		steps += 1
	Input.action_release("move_right")
	await get_tree().physics_frame
	assert_float(scene.player.position.x).is_greater_equal(80.0)
	assert_int(scene.request(&"interact")).is_equal(RoundRules.Result.ACCEPTED)
	assert_bool(scene.target.visible).is_false()
	scene.pause_button.pressed.emit()
	var position: Vector2 = scene.player.position
	var elapsed: float = scene.rules.view().elapsed
	Input.action_press("move_right")
	for _frame: int in range(5):
		await get_tree().physics_frame
	assert_vector(scene.player.position).is_equal(position)
	assert_float(scene.rules.view().elapsed).is_equal(elapsed)
	Input.action_release("move_right")
	scene.pause_button.pressed.emit()
	await get_tree().physics_frame
	await get_tree().physics_frame
	assert_float(scene.rules.view().elapsed).is_greater(elapsed)
	for _index: int in range(3):
		scene.request(&"pause")
		scene.restart_button.pressed.emit()
		assert_bool(get_tree().paused).is_false()
		assert_vector(scene.player.position).is_equal(Vector2.ZERO)
		assert_bool(scene.rules.view().activated).is_false()
		assert_bool(scene.target.visible).is_true()
	assert_int(scene.world.get_child_count()).is_equal(7)
	var snapshot: Dictionary = scene.diagnostic_snapshot()
	assert_str(snapshot.route).is_equal("2d")
	assert_str(snapshot.distance_unit).is_equal("px")
	assert_array(snapshot.position).has_size(2)


func test_four_walls_and_diagonal_speed_use_engine_physics() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://scenes/main_2d.tscn")
	var scene: StarterMain2D = runner.scene() as StarterMain2D
	scene.request(&"start")
	for action: String in ["move_right", "move_left", "move_forward", "move_back"]:
		scene.request(&"restart")
		Input.action_press(action)
		for _frame: int in range(120):
			await get_tree().physics_frame
		Input.action_release(action)
		var point: Vector2 = scene.player.position
		if action == "move_right":
			assert_float(point.x).is_between(273.0, 275.0)
		elif action == "move_left":
			assert_float(point.x).is_between(-275.0, -273.0)
		elif action == "move_forward":
			assert_float(point.y).is_between(-175.0, -173.0)
		else:
			assert_float(point.y).is_between(173.0, 175.0)
	scene.request(&"restart")
	Input.action_press("move_right")
	Input.action_press("move_back")
	for _frame: int in range(12):
		await get_tree().physics_frame
	assert_float(scene.player.velocity.length()).is_equal_approx(200.0, 0.001)
	assert_float(scene.player.position.x).is_greater(0.0)
	assert_float(scene.player.position.y).is_greater(0.0)
	assert_float(scene.player.position.length()).is_between(33.0, 44.0)


func test_slow_preset_actual_movement_and_shared_font() -> void:
	var packed: PackedScene = load("res://scenes/main_2d.tscn") as PackedScene
	var instance: StarterMain2D = auto_free(packed.instantiate()) as StarterMain2D
	instance.tuning = load("res://tuning/slow_2d.tres") as StarterTuning
	var runner: GdUnitSceneRunner = scene_runner(instance)
	var scene: StarterMain2D = runner.scene() as StarterMain2D
	assert_float(scene.player.move_speed).is_equal(100.0)
	scene.start_button.pressed.emit()
	Input.action_press("move_right")
	for _frame: int in range(12):
		await get_tree().physics_frame
	Input.action_release("move_right")
	assert_float(scene.player.position.x).is_between(15.0, 23.0)
	var baseline: StarterTuning = load("res://tuning/baseline_2d.tres") as StarterTuning
	assert_float(baseline.move_speed).is_equal(200.0)
	var panel: PanelContainer = scene.get_node("Interface/Panel") as PanelContainer
	assert_object(panel.theme.default_font).is_null()
	assert_object(scene.status.get_theme_font("font")).is_same(ThemeDB.fallback_font)
	assert_int(scene.status.get_theme_font_size("font_size")).is_equal(22)


func test_presentation_and_view_do_not_own_gameplay() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://scenes/main_2d.tscn")
	var scene: StarterMain2D = runner.scene() as StarterMain2D
	var presenter: StarterPresentation2D = Presentation.new(scene.world, scene.target, scene.status,
		scene.start_button, scene.pause_button, scene.restart_button)
	for action: StringName in [&"start", &"interact", &"pause", &"continue", &"restart"]:
		scene.request(action)
		var view: Dictionary = scene.rules.view()
		var before: Dictionary = scene.diagnostic_snapshot()
		var velocity: Vector2 = scene.player.velocity
		var direction: Vector2 = scene.player.direction
		var paused: bool = get_tree().paused
		presenter.present(view)
		var text: String = scene.status.text
		presenter.present(view)
		assert_str(scene.status.text).is_equal(text)
		assert_bool(get_tree().paused).is_equal(paused)
		assert_vector(scene.player.velocity).is_equal(velocity)
		assert_vector(scene.player.direction).is_equal(direction)
		assert_dict(scene.diagnostic_snapshot()).is_equal(before)
		assert_dict(view).is_equal(before.state)
		assert_bool(scene.world.visible).is_equal(view.running)
		assert_bool(scene.target.visible).is_equal(not view.activated)
		assert_bool(scene.start_button.visible).is_equal(not view.running)
		assert_bool(scene.pause_button.visible).is_equal(view.running)
		assert_bool(scene.restart_button.visible).is_equal(view.running)
	scene.player.position = Vector2(100.0, 0.0)
	assert_int(scene.request(&"interact")).is_equal(RoundRules.Result.ACCEPTED)
	var before: Dictionary = scene.diagnostic_snapshot()
	scene.target.visible = true
	presenter.present(scene.rules.view())
	assert_bool(scene.target.visible).is_false()
	assert_dict(scene.diagnostic_snapshot()).is_equal(before)
	var detached: Dictionary = scene.rules.view()
	detached.running = false
	detached.activated = false
	detached.elapsed = 999.0
	assert_dict(scene.rules.view()).is_equal(before.state)


func test_capture_points_include_canvas_transform() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://scenes/main_2d.tscn")
	var scene: StarterMain2D = runner.scene() as StarterMain2D
	scene.request(&"start")
	var points: Dictionary = scene.capture_points()
	assert_vector(points.actor).is_equal(Vector2(480.0, 420.0))
	assert_vector(points.target).is_equal(Vector2(630.0, 420.0))
	scene.get_viewport().canvas_transform = Transform2D(0.0, Vector2(1.5, 1.5), 0.0, Vector2(12.0, 20.0))
	points = scene.capture_points()
	assert_vector(points.actor).is_equal(Vector2(732.0, 650.0))
	assert_vector(points.target).is_equal(Vector2(957.0, 650.0))
	scene.get_viewport().canvas_transform = Transform2D.IDENTITY
