$(document).ready(function() {
	uri = "ws://127.0.0.1:9000/user/adityapc/api/kernels/{kernel_id}/channels"
	Socket = new WebSocket(
      ws_scheme + window.location.host + '/ws/quiz'
    );
    Socket.onmessage = function(e) {
      const data = JSON.parse(e);
      console.log(data)
    };

    Socket.onclose = function(e) {
      unlock_screen();
      console.error('Chat socket closed unexpectedly');
    };


});