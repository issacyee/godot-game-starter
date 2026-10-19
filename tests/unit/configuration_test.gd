extends GdUnitTestSuite

const Tuning = preload("res://scripts/starter_tuning.gd")
const Journal = preload("res://scripts/diagnostic_journal.gd")


func test_tuning_validation_and_value_isolation() -> void:
	var tuning := Tuning.new()
	assert_array(Array(tuning.validate())).is_empty()
	var values: Dictionary = tuning.effective_values()
	values.move_speed = 8.0
	assert_float(tuning.move_speed).is_equal(4.0)
	tuning.move_speed = NAN
	assert_array(Array(tuning.validate())).has_size(1)
	tuning.interaction_reach = 3.0
	assert_array(Array(tuning.validate())).has_size(2)


func test_route_parameters_are_validated_without_unit_confusion() -> void:
	var tuning := Tuning.new()
	assert_array(Array(tuning.validate_for("2d"))).is_not_empty()
	tuning.route = "2d"
	assert_array(Array(tuning.validate())).is_not_empty()
	tuning.move_speed = 200.0
	tuning.interaction_reach = 75.0
	assert_array(Array(tuning.validate_for("2d"))).is_empty()
	assert_array(Array(tuning.validate_for("3d"))).has_size(1)
	tuning.move_speed = INF
	assert_array(Array(tuning.validate())).has_size(1)
	tuning.route = "unknown"
	assert_array(Array(tuning.validate())).is_not_empty()


func test_diagnostics_bounded_and_no_mutable_escape() -> void:
	var journal := Journal.new(2)
	journal.record(&"start", 0)
	journal.record(&"interact", 3)
	journal.record(&"pause", 0)
	var snapshot: Dictionary = journal.snapshot()
	assert_int(snapshot.dropped).is_equal(1)
	assert_int(snapshot.events[0].sequence).is_equal(2)
	snapshot.events.clear()
	assert_array(journal.snapshot().events).has_size(2)
