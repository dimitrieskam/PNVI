extends Node3D

func _ready():
	make_static(self)

func make_static(node: Node):
	if node is MeshInstance3D:
		# Create a StaticBody3D
		var static_body = StaticBody3D.new()
		node.get_parent().add_child(static_body)
		static_body.global_transform = node.global_transform  # Keep position
		
		# Reparent MeshInstance3D under StaticBody3D
		node.get_parent().remove_child(node)
		static_body.add_child(node)
		node.owner = static_body  # Set correct scene ownership

		# Set GI mode for better rendering
		node.gi_mode = GeometryInstance3D.GI_MODE_STATIC
		
		# Add a collision shape (optional)
		var collision = CollisionShape3D.new()
		var shape = BoxShape3D.new()
		shape.size = node.get_aabb().size  # Approximate collision size
		collision.shape = shape
		static_body.add_child(collision)

	for child in node.get_children():
		make_static(child)
