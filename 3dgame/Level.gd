extends Node3D

@onready var timer = $TimerGame
@onready var timer_label = $Control/Timer

var coins_collected = 0
var total_coins = 0

const WIN_SCENE = preload("res://assets/you-win.tscn")
const LOST_SCENE = preload("res://assets/game-over.tscn")

# Called when the node enters the scene tree for the first time.
func _ready():
	total_coins = get_tree().get_nodes_in_group("coins").size()
	print("Total coins in the scene: ", total_coins)  # Debugging output
	# Start and connect the timer
	timer.start()
	timer.timeout.connect(_on_timer_game_timeout)
	
	# Connect each coin's signal
	for coin in get_tree().get_nodes_in_group("coins"):
		coin.connect("coinCollected", _on_coin_collected)



# Called when a coin is collected
func _on_coin_collected():
	coins_collected += 1
	print("Coins collected:", coins_collected, "/", total_coins)  # Debugging output

	if coins_collected >= total_coins:
		show_end_screen(true)  # Show the winning screen
# Show end screen (Win or Lose)
func show_end_screen(won: bool):
	get_tree().paused = false
	var scene_to_load = WIN_SCENE if won else LOST_SCENE
	get_tree().change_scene_to_packed(scene_to_load)
	
	


func _on_timer_game_timeout() -> void:
		show_end_screen(false)  # Show the losing screen
