extends Area3D

signal coinCollected

func _physics_process(delta):
	rotate_y(deg_to_rad(3))
	
func _on_body_entered(body: Node3D) -> void:
	
	$Timer.start()
	

func _on_timer_timeout() -> void:
	emit_signal("coinCollected")
	queue_free()
	

func _ready():
	add_to_group("player")
#
#
#
#
#func _on_area_entered(area: Area3D):
		#$AudioStreamPlayer3D.play()
		#await $AudioStreamPlayer3D.finished
		#get_parent().collect_treasure()
		#queue_free()
