# Tree.gd
extends Node3D

func _ready():
	# Randomly rotate the tree for variety
	rotation.y = randf_range(0, PI * 2)
	# Randomly scale the tree slightly
	var scale_factor = randf_range(0.8, 1.2)
	scale = Vector3.ONE * scale_factor
