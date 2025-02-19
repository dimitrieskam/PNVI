extends CharacterBody3D

const SPEED = 5.0

func _physics_process(delta):
	var input_dir = Vector3.ZERO

	# Capture movement input
	if Input.is_action_pressed("ui_right"):
		input_dir.x += 1
	if Input.is_action_pressed("ui_left"):
		input_dir.x -= 1
	if Input.is_action_pressed("ui_up"):
		input_dir.z -= 1
	if Input.is_action_pressed("ui_down"):
		input_dir.z += 1

	# Normalize to prevent faster diagonal movement
	if input_dir != Vector3.ZERO:
		input_dir = input_dir.normalized() * SPEED

	velocity.x = input_dir.x
	velocity.z = input_dir.z

	move_and_slide()

	# Debugging output
	print("Player Position:", global_transform.origin, " Velocity:", velocity)
