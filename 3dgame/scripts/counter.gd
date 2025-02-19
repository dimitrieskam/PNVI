extends Label

var coins = 0 

 

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	update_coin_text()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass


func _on_coin_collected() -> void:
	coins = coins + 1
	update_coin_text()

func update_coin_text():
	text = str(coins)
