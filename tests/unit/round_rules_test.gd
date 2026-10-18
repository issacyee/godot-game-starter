extends GdUnitTestSuite

const Rules = preload("res://scripts/round_rules.gd")


func test_inactive_and_reset() -> void:
	var rules := Rules.new(1.5)
	assert_int(rules.interact(0.0)).is_equal(Rules.Result.INACTIVE)
	rules.start()
	assert_int(rules.interact(0.0)).is_equal(Rules.Result.ACCEPTED)
	rules.advance(2.0)
	rules.start()
	assert_dict(rules.view()).is_equal({"running": true, "paused": false, "activated": false, "elapsed": 0.0})


func test_range_boundary_and_rejection() -> void:
	var rules := Rules.new(1.5)
	rules.start()
	assert_int(rules.interact(1.5001)).is_equal(Rules.Result.OUT_OF_RANGE)
	assert_bool(rules.view().activated).is_false()
	assert_int(rules.interact(1.5)).is_equal(Rules.Result.ACCEPTED)
	assert_int(rules.interact(0.0)).is_equal(Rules.Result.ALREADY_ACTIVATED)


func test_pause_time_and_resume() -> void:
	var rules := Rules.new()
	rules.start()
	assert_bool(rules.advance(0.25)).is_true()
	rules.set_paused(true)
	assert_int(rules.interact(0.0)).is_equal(Rules.Result.PAUSED)
	rules.advance(20.0)
	assert_float(rules.view().elapsed).is_equal(0.25)
	rules.set_paused(false)
	rules.advance(0.5)
	assert_float(rules.view().elapsed).is_equal(0.75)


func test_invalid_time_and_distance_do_not_mutate() -> void:
	var rules := Rules.new()
	rules.start()
	var before: Dictionary = rules.view()
	for seconds: float in [-1.0, INF, NAN]:
		assert_bool(rules.advance(seconds)).is_false()
	for distance: float in [-0.1, INF, NAN]:
		assert_int(rules.interact(distance)).is_equal(Rules.Result.INVALID)
	assert_dict(rules.view()).is_equal(before)


func test_activation_event_only_once() -> void:
	var rules := Rules.new()
	var events: Array[int] = []
	rules.activated.connect(func() -> void: events.append(1))
	rules.start()
	rules.interact(1.6)
	rules.interact(1.0)
	rules.interact(0.0)
	assert_array(events).is_equal([1])
