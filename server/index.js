var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var path = require('path');
var root_dir = path.join(__dirname, '../');
const util = require('util')
app.use(express.static(root_dir+'/client/'));
var io_web = io.of('/web_channel');

var io_automation = io.of('/automation_channel');
var data_server_data=[]

var direct_forward_events_to_driver ={}

var connected_features = {}

var port = process.env.PORT || 8080;
server.listen(port);

app.get('*', function (req, res) {
    console.log("http connection request...");
    res.sendFile(root_dir+'/client/index.html');
});

var send_msg = function(_receiving_channel,event_type,msg){
	if(msg=='undefined'){
		return
	}
    _receiving_channel.emit(event_type,msg);
    console.log(event_type+" "+msg );
}

var setCB = function(_event,_socket_from,_socket_to) {
    _socket_from.on(_event, function(_data) {
		console.log(_event)
		send_msg(_socket_to,_event,_data)
    });
};

var regsiter_direct_forward_events_to_driver =function(){
	Object.keys(direct_forward_events_to_driver).forEach(function(key) {
		var value = direct_forward_events_to_driver[key];
		for(var i=value['direct_forward_events_to_driver'].length-1;i>=0;i--){
			var event_type =value['direct_forward_events_to_driver'][i];
			var sockets = io_web.sockets;
			for(var socketId in sockets){
  				var socket = sockets[socketId];
				setCB(event_type,socket,value['socket'])
			}
		}
	});
}

var register_direct_forward_events = function(_socket,_driver_channel){
	send_msg(_socket,'get_direct_forward_events','')
	_socket.on('direct_forward_events_to_web',function(_direct_forward_events){
		//console.log(util.inspect(_direct_forward_events, {showHidden: false, depth: null}))
		for(var i=0;i<_direct_forward_events.length;i++){
			var event_type =_direct_forward_events[i]
			setCB(event_type,_socket,io_web)
		}
  	});

	_socket.on('direct_forward_events_to_driver',function(_direct_forward_events){
		direct_forward_events_to_driver[_socket.id] =
		{'socket':_socket,'direct_forward_events_to_driver':_direct_forward_events}
		regsiter_direct_forward_events_to_driver()
  	});

	_socket.on('disconnect', function() {
		delete direct_forward_events_to_driver[_socket.id];
      	console.log('Got disconnect!');
   });
}
var send_connected_features = function(_channel){
	send_msg(_channel,'active_features',connected_features)
}
// ---------------------------web channel-------------------------------------
io_web.on('connection',function(socket){
	var clientIp = socket.request.connection.remoteAddress
	console.log(clientIp+ " at : "+ socket.id);

	regsiter_direct_forward_events_to_driver()

	socket.on('get_active_features',function(_data){
    	send_connected_features(socket)
  	});
});

// ----------------------home automation channel-----------------------
io_automation.on('connection',function(socket){
	var clientIp = socket.request.connection.remoteAddress
	console.log("connected to automation driver :" + clientIp+ " at : "+ socket.id);
	send_msg(socket,'get_feature_name','')
	socket.on('set_feature_name',function(_data){
		console.log('connected feature : '+_data.name)
		connected_features[socket.id]={name:_data.name,info:_data.info,web_path:_data.web_path}
		send_connected_features(io_web)
	})
	socket.on('disconnect', function() {
		delete connected_features[socket.id];
		send_connected_features(io_web)
      	console.log('Got disconnect!');
  	});
	register_direct_forward_events(socket)
});


console.log("listenning on "+ port);
