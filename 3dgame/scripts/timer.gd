extends Label

var time_elapsed: float = 40.0
var counting: bool = false  # Controls whether the timer is running

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	text = "TIME: 0"
	counting = true  # Start counting when the game starts

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	if counting:
		time_elapsed -= delta
		text = "TIME: " + str(int(time_elapsed))  # Display time as whole seconds
