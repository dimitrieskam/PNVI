extends StaticBody3D


func _ready():
	# Optional: Add random rotation for variety
	rotation.y = randf_range(0, PI)
