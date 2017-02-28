var five = require('johnny-five');
var board = new five.Board();

board.on('ready', function() {
  var led = new five.Led(2); // pin 13
  led.blink(500); // 500ms interval
	console.log("blinking")
});
