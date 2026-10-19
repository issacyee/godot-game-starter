extends GdUnitTestSuite


func test_project_route_is_explicit_and_matches_main_scene() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://starter-project.json"))
	assert_float(config.schema).is_equal(1.0)
	assert_bool(config.route in ["template", "2d", "3d"]).is_true()
	var expected: String = "res://scenes/main.tscn" if config.route == "3d" else "res://scenes/main_2d.tscn"
	assert_str(ProjectSettings.get_setting("application/run/main_scene")).is_equal(expected)
