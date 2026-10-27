extends Node2D

const WIDTH := 960.0
const HEIGHT := 540.0
const FLOOR_Y := 425.0
const PLAYER_X := 180.0
const CEILING_Y := 112.0
const GRAVITY := 1350.0
const JUMP_SPEED := -570.0
const AIR_DASH_BONUS := 110.0
const AIR_DASH_DURATION := 0.18
const SHIP_PATH := "res://assets/ship.svg"
const EASTER_EGG_PATH := "res://assets/easter_egg.jpg"
const RECORD_PATH := "user://pulso_record.cfg"

var player_y := FLOOR_Y - 22.0
var velocity_y := 0.0
var speed := 300.0
var distance := 0.0
var score := 0
var best_score := 0
var pulse_flash := 0.0
var elapsed_time := 0.0
var air_dash_used := false
var air_dash_timer := 0.0
var game_over := false
var started := false
var obstacles: Array[Dictionary] = []
var crystals: Array[Dictionary] = []
var stars: Array[Vector2] = []
var music: AudioStreamPlayer
var pulse_sound: AudioStreamPlayer
var collect_sound: AudioStreamPlayer
var crash_sound: AudioStreamPlayer
var ship_sprite: Sprite2D
var easter_egg_sprite: Sprite2D

func _ready() -> void:
	for i in range(55):
		stars.append(Vector2(randf_range(0, WIDTH), randf_range(20, FLOOR_Y - 40)))
	_reset_obstacles()
	_reset_crystals()
	_load_record()
	ship_sprite = Sprite2D.new()
	ship_sprite.texture = load(SHIP_PATH)
	ship_sprite.scale = Vector2(0.42, 0.42)
	add_child(ship_sprite)
	easter_egg_sprite = Sprite2D.new()
	easter_egg_sprite.texture = load(EASTER_EGG_PATH)
	easter_egg_sprite.scale = Vector2(0.42, 0.42)
	var moon_shader := Shader.new()
	moon_shader.code = """
shader_type canvas_item;
void fragment() {
	vec2 centered_uv = UV - vec2(0.5);
	float radius = length(centered_uv);
	if (radius > 0.5) {
		discard;
	}
	vec4 photo = texture(TEXTURE, UV);
	float rim = smoothstep(0.36, 0.5, radius);
	photo.rgb = mix(photo.rgb, vec3(0.62, 0.82, 1.0), 0.12) + rim * vec3(0.12, 0.22, 0.38);
	COLOR = photo;
}
"""
	var moon_material := ShaderMaterial.new()
	moon_material.shader = moon_shader
	easter_egg_sprite.material = moon_material
	add_child(easter_egg_sprite)
	music = AudioStreamPlayer.new()
	music.volume_db = -15.0
	add_child(music)
	music.stream = _make_music()
	music.finished.connect(_loop_music)
	music.play()
	pulse_sound = _make_sound(620.0, 0.0, 0.11, 0.12)
	collect_sound = _make_sound(880.0, 1320.0, 0.16, 0.16)
	crash_sound = _make_sound(150.0, 72.0, 0.28, 0.2, 0.55)
	add_child(pulse_sound)
	add_child(collect_sound)
	add_child(crash_sound)

func _make_sound(frequency: float, second_frequency: float, duration: float, volume: float, fall: float = 0.0) -> AudioStreamPlayer:
	var sample_rate := 22050
	var sample_count := int(sample_rate * duration)
	var pcm := PackedByteArray()
	pcm.resize(sample_count * 2)
	for i in range(sample_count):
		var t := float(i) / sample_rate
		var envelope := pow(1.0 - float(i) / sample_count, 2.0)
		var current_frequency := frequency * (1.0 - fall * float(i) / sample_count)
		var sample := sin(TAU * current_frequency * t)
		if second_frequency > 0.0:
			sample = (sample + sin(TAU * second_frequency * t)) * 0.5
		pcm.encode_s16(i * 2, int(sample * envelope * volume * 32767.0))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.stereo = false
	stream.data = pcm
	var player := AudioStreamPlayer.new()
	player.stream = stream
	player.volume_db = -3.0
	return player

func _make_music() -> AudioStreamWAV:
	# Pequena melodia ambiente gerada pelo próprio jogo, sem arquivos extras.
	var sample_rate := 22050
	var beat := 0.32
	var notes := [220.0, 261.63, 329.63, 293.66, 196.0, 246.94, 293.66, 261.63]
	var samples_per_note := int(sample_rate * beat)
	var pcm := PackedByteArray()
	pcm.resize(samples_per_note * notes.size() * 2)
	for note_index in range(notes.size()):
		for i in range(samples_per_note):
			var t := float(i) / sample_rate
			var fade := minf(1.0, float(i) / 300.0) * minf(1.0, float(samples_per_note - i) / 1200.0)
			var tone := sin(TAU * notes[note_index] * t) * 0.12
			var overtone := sin(TAU * notes[note_index] * 2.0 * t) * 0.035
			var sample := (tone + overtone) * fade
			pcm.encode_s16((note_index * samples_per_note + i) * 2, int(sample * 32767.0))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.stereo = false
	stream.data = pcm
	return stream

func _loop_music() -> void:
	if music.stream != null:
		music.play()

func _input(event: InputEvent) -> void:
	var pressed: bool = (event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_SPACE) or (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT)
	if not pressed:
		return
	if game_over:
		_restart()
		return
	started = true
	pulse_flash = 0.16
	pulse_sound.play()
	if player_y >= FLOOR_Y - 22.0:
		velocity_y = JUMP_SPEED
		air_dash_used = false
	elif not air_dash_used:
		air_dash_used = true
		air_dash_timer = AIR_DASH_DURATION

func _process(delta: float) -> void:
	elapsed_time += delta
	pulse_flash = maxf(0.0, pulse_flash - delta)
	if started and not game_over:
		speed = minf(320.0 + distance * 0.014, 440.0)
		var scroll_speed := speed
		if air_dash_timer > 0.0:
			scroll_speed = minf(speed + AIR_DASH_BONUS, 460.0)
			air_dash_timer = maxf(0.0, air_dash_timer - delta)
		distance += scroll_speed * delta
		velocity_y += GRAVITY * delta
		player_y += velocity_y * delta
		if player_y > FLOOR_Y - 22.0:
			player_y = FLOOR_Y - 22.0
			velocity_y = 0.0
			air_dash_used = false
		if player_y < CEILING_Y:
			player_y = CEILING_Y
			velocity_y = 0.0
		for obstacle in obstacles:
			obstacle.x -= scroll_speed * delta
			if not game_over and _hits_obstacle(obstacle):
				game_over = true
				crash_sound.play()
		for i in range(obstacles.size()):
			if obstacles[i].x < -100:
				obstacles[i] = _new_obstacle(_next_obstacle_spawn_x())
		for crystal in crystals:
			crystal.x -= scroll_speed * delta
			if crystal.active and Vector2(PLAYER_X, player_y).distance_to(Vector2(crystal.x, crystal.y)) < 72.0:
				crystal.active = false
				score += 100
				collect_sound.play()
			if crystal.x < -30.0:
				crystal.x = _next_crystal_spawn_x()
				crystal.y = randf_range(300.0, 365.0)
				crystal.active = true
		if game_over and score > best_score:
			best_score = score
			_save_record()
	queue_redraw()

func _hits_obstacle(obstacle: Dictionary) -> bool:
	var px1 := PLAYER_X - 19.0
	var px2 := PLAYER_X + 19.0
	var py1 := player_y - 18.0
	var py2 := player_y + 18.0
	var ox1: float = obstacle.x
	var ox2: float = obstacle.x + obstacle.w
	var oy1: float = FLOOR_Y - obstacle.h
	return px1 < ox2 and px2 > ox1 and py1 < FLOOR_Y and py2 > oy1

func _reset_obstacles() -> void:
	obstacles = [
		{"x": 640.0, "w": 46.0, "h": 66.0, "kind": 0},
		{"x": 1150.0, "w": 50.0, "h": 82.0, "kind": 1},
		{"x": 1680.0, "w": 46.0, "h": 74.0, "kind": 2},
		{"x": 2220.0, "w": 54.0, "h": 92.0, "kind": 0},
		{"x": 2760.0, "w": 48.0, "h": 80.0, "kind": 1},
	]

func _new_obstacle(x: float) -> Dictionary:
	return {"x": x, "w": randf_range(42.0, 54.0), "h": randf_range(62.0, 94.0), "kind": randi_range(0, 2)}

func _next_obstacle_spawn_x() -> float:
	var farthest_x := WIDTH
	for obstacle in obstacles:
		if obstacle.x > -100.0:
			farthest_x = maxf(farthest_x, obstacle.x)
	return farthest_x + randf_range(455.0, 515.0)

func _next_crystal_spawn_x() -> float:
	var farthest_x := WIDTH
	for obstacle in obstacles:
		if obstacle.x > -100.0:
			farthest_x = maxf(farthest_x, obstacle.x)
	for crystal in crystals:
		if crystal.active and crystal.x > -30.0:
			farthest_x = maxf(farthest_x, crystal.x)
	return farthest_x + randf_range(220.0, 320.0)

func _reset_crystals() -> void:
	crystals = [
		{"x": 880.0, "y": 345.0, "active": true},
		{"x": 1400.0, "y": 330.0, "active": true},
		{"x": 1930.0, "y": 350.0, "active": true},
		{"x": 2470.0, "y": 320.0, "active": true},
		{"x": 3000.0, "y": 340.0, "active": true},
	]

func _load_record() -> void:
	var config := ConfigFile.new()
	if config.load(RECORD_PATH) == OK:
		best_score = int(config.get_value("record", "best_score", 0))

func _save_record() -> void:
	var config := ConfigFile.new()
	config.set_value("record", "best_score", best_score)
	config.save(RECORD_PATH)

func _restart() -> void:
	player_y = FLOOR_Y - 22.0
	velocity_y = 0.0
	air_dash_used = false
	air_dash_timer = 0.0
	speed = 320.0
	distance = 0.0
	score = 0
	game_over = false
	started = false
	_reset_obstacles()
	_reset_crystals()

func _draw() -> void:
	var stage := int(distance / 2500.0) % 4
	var sky_colors: Array[Color] = [Color("080d25"), Color("101b36"), Color("251638"), Color("092b35")]
	var floor_colors: Array[Color] = [Color("111a3b"), Color("182b49"), Color("342047"), Color("10404a")]
	var hazard_colors: Array[Color] = [Color("f15b78"), Color("ff9d4d"), Color("d66aff"), Color("ffc857")]
	var star_colors: Array[Color] = [Color("8ebcff"), Color("a4d5ff"), Color("ffc8ff"), Color("a5fff0")]
	var hazard_color: Color = hazard_colors[stage]
	draw_rect(Rect2(0, 0, WIDTH, HEIGHT), sky_colors[stage])
	for i in range(stars.size()):
		var p := stars[i]
		var x := fposmod(p.x - distance * (0.08 + float(i % 4) * 0.025), WIDTH)
		var star_color := star_colors[stage]
		star_color.a = 0.35 + float(i % 4) * 0.12
		draw_circle(Vector2(x, p.y), 1.0 + float(i % 3) * 0.45, star_color)
	# distant horizon and floor
	draw_rect(Rect2(0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y), floor_colors[stage])
	draw_line(Vector2(0, FLOOR_Y), Vector2(WIDTH, FLOOR_Y), star_colors[stage], 3.0)
	for i in range(22):
		var x := fposmod(float(i * 64) - distance * 0.7, WIDTH)
		draw_line(Vector2(x, FLOOR_Y + 1), Vector2(x - 28, HEIGHT), Color(0.16, 0.35, 0.57, 0.36), 1.0)
	# obstacles
	for obstacle in obstacles:
		var rect := Rect2(obstacle.x, FLOOR_Y - obstacle.h, obstacle.w, obstacle.h)
		if obstacle.kind == 1:
			var spike_count := 2
			var points := PackedVector2Array([Vector2(rect.position.x, FLOOR_Y), Vector2(rect.position.x + rect.size.x * 0.5, rect.position.y), Vector2(rect.position.x + rect.size.x, FLOOR_Y)])
			draw_colored_polygon(points, hazard_color)
			for spike_index in range(spike_count):
				var sx := rect.position.x + rect.size.x * float(spike_index + 1) / float(spike_count + 1)
				draw_line(Vector2(sx, rect.position.y + 10), Vector2(sx, FLOOR_Y - 5), hazard_color.lightened(0.35), 2.0)
		elif obstacle.kind == 2:
			draw_rect(rect, hazard_color.darkened(0.3))
			draw_rect(Rect2(rect.position.x + 5, rect.position.y + 8, rect.size.x - 10, rect.size.y - 16), hazard_color)
			draw_line(Vector2(rect.position.x + 3, rect.position.y + 8), Vector2(rect.position.x + rect.size.x - 3, rect.position.y + 8), Color.WHITE, 2.0)
		else:
			draw_rect(rect, hazard_color)
			draw_rect(Rect2(rect.position.x + 6, rect.position.y + 7, rect.size.x - 12, rect.size.y - 7), hazard_color.darkened(0.45))
	for crystal in crystals:
		if crystal.active:
			var point := Vector2(crystal.x, crystal.y)
			draw_circle(point, 15.0, Color(0.2, 0.95, 1.0, 0.18))
			draw_colored_polygon(PackedVector2Array([point + Vector2(0, -12), point + Vector2(9, 0), point + Vector2(0, 12), point + Vector2(-9, 0)]), Color("79ffff"))
			draw_colored_polygon(PackedVector2Array([point + Vector2(0, -7), point + Vector2(5, 0), point + Vector2(0, 7), point + Vector2(-5, 0)]), Color("eaffff"))
	# Nave em sprite vetorial
	var ship := Vector2(PLAYER_X, player_y)
	ship_sprite.position = ship
	# Easter egg: a cabeça flutua como uma lua no canto superior direito.
	var moon_position := Vector2(WIDTH - 78.0, 82.0 + sin(elapsed_time * 1.6) * 7.0)
	draw_circle(moon_position, 56.0, Color(0.28, 0.72, 1.0, 0.12))
	draw_arc(moon_position, 52.0, 0.0, TAU, 64, Color(0.55, 0.85, 1.0, 0.55), 2.0)
	draw_circle(moon_position + Vector2(44.0, -35.0), 2.0, Color("bafaff"))
	draw_circle(moon_position + Vector2(-48.0, 27.0), 1.7, Color("bafaff"))
	easter_egg_sprite.position = moon_position
	if pulse_flash > 0.0:
		draw_circle(ship, 54.0 * pulse_flash / 0.16 + 13.0, Color(0.15, 0.9, 1.0, 0.12))
		draw_arc(ship, 24.0 + 48.0 * pulse_flash / 0.16, 0, TAU, 48, Color("53f6ff"), 3.0)
	if air_dash_timer > 0.0:
		for streak in range(3):
			var streak_y := ship.y - 10.0 + float(streak) * 10.0
			draw_line(Vector2(ship.x - 24.0, streak_y), Vector2(ship.x - 68.0 - float(streak) * 8.0, streak_y), Color(0.25, 0.9, 1.0, 0.75), 2.0)
	# UI
	draw_string(ThemeDB.fallback_font, Vector2(30, 42), "P U L S O", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color("8bf7ff"))
	draw_string(ThemeDB.fallback_font, Vector2(30, 72), "DISTÂNCIA  %04d m" % int(distance / 10.0), HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color("c8d8ff"))
	draw_string(ThemeDB.fallback_font, Vector2(30, 98), "CRISTAIS  %d    •    RECORDE  %d" % [score / 100, best_score / 100], HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color("79ffff"))
	draw_string(ThemeDB.fallback_font, Vector2(585, 42), "ESPAÇO / CLIQUE  •  PULSO", HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color("c8d8ff"))
	if not started and not game_over:
		_draw_center_text("P U L S O", 215, 42, Color("8bf7ff"))
		_draw_center_text("APERTE ESPAÇO OU CLIQUE", 270, 24, Color("ffffff"))
		_draw_center_text("No chão: salta   •   No ar: avanço rápido   •   Colete cristais", 308, 17, Color("9db6e9"))
		_draw_center_text("Recorde: %d cristais" % [best_score / 100], 338, 16, Color("79ffff"))
	if game_over:
		draw_rect(Rect2(0, 0, WIDTH, HEIGHT), Color(0.02, 0.02, 0.08, 0.72))
		_draw_center_text("SINAL PERDIDO", 248, 34, Color("ff7895"))
		_draw_center_text("Cristais: %d     •     Recorde: %d" % [score / 100, best_score / 100], 278, 21, Color("79ffff"))
		_draw_center_text("Aperte espaço ou clique para tentar de novo", 316, 18, Color("ffffff"))

func _draw_center_text(message: String, y: float, size: int, color: Color) -> void:
	var width := ThemeDB.fallback_font.get_string_size(message, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	draw_string(ThemeDB.fallback_font, Vector2((WIDTH - width) / 2.0, y), message, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)
