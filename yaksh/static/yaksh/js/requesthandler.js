request_status = "initial";
count = 0;
MAX_COUNT = 14

function reset_values() {
    request_status = "initial";
    count = 0;
}
function check_state(state, uid) {
    if ((state == "running" || state == "not started") && count < MAX_COUNT) {
        count++;
        setTimeout(function() {get_result(uid);}, 2000);
    } else if (state == "unknown") {
        reset_values();
        notify("Request timeout. Try again later.");
        unlock_screen();
    } else {
        reset_values()
        notify("Please try again.");
        unlock_screen();
    }
}

function notify(text) {
    var notice = document.getElementById("notification");
    notice.classList.add("alert");
    notice.classList.add("alert-success");
    notice.innerHTML = text;
}

function lock_screen() {
    document.getElementById("ontop").style.display = "block";
}

function unlock_screen() {
    document.getElementById("ontop").style.display = "none";
}

function show_solution() {
    var solution = document.getElementById("solution");
    solution.style.display = "block";
    solution.className ="well well-sm";
    document.getElementById("skip_ex").style.visibility = "visible";
}

function get_result(uid){
    var url = "/exam/get_result/" + uid + "/" + course_id + "/" + module_id + "/";
    ajax_check_code(url, "GET", "html", null, uid)
}

function response_handler(method_type, content_type, data, uid){
    if(content_type.indexOf("text/html") !== -1) {
        if( method_type === "POST") {
            reset_values();
        }
        unlock_screen();
        document.open();
        document.write(data);
        document.close();
    } else if(content_type.indexOf("application/json") !== -1) {
        res = JSON.parse(data);
        request_status = res.status;
        if (request_status){
          if(method_type === "POST") {
              uid = res.uid;
          }
          var code = global_editor.editor.getValue();
          ws_data = {'code': code, 'kernel_id': kernel_id,
                     'result': res}
          lock_screen();
          Socket.send(JSON.stringify(ws_data));
        }
        else{
          unlock_screen();
          if ($("#notification")){
            $("#notification").toggle();
          }

          var error_output = document.getElementById("error_panel");
          error_output.innerHTML = res.error;
          focus_on_error(error_output);
        }
    } else {
        reset_values();
        unlock_screen();
    }
}

function focus_on_error(ele){
    if (ele) {
      ele.scrollIntoView(true);
      window.scrollBy(0, -15);
        }
    }
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function ajax_check_code(url, method_type, data_type, data, uid)
 {
    var ajax_post_data = {
        "method": method_type,
        "url": url,
        "data": data,
        "dataType": data_type,
        "async": false,
        "beforeSend": function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
          }
        },
        "success": function(data, status, xhr) {
            content_type = xhr.getResponseHeader("content-type");
            response_handler(method_type, content_type, data, uid)
        },
        "error": function(xhr, text_status, error_thrown ) {
            reset_values();
            unlock_screen();
            notify("There is some problem. Try later.")
        }
    }
    if (question_type == "upload"){
        ajax_post_data["processData"] = false;
        ajax_post_data["contentType"] = false;
    }
    $.ajax(ajax_post_data);

}

var global_editor = {};
var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();

var ws_scheme = window.location.protocol == "https:" ? "wss://" : "ws://";
var Socket;

$(window).on('unload', function() {
  // do something
  navigator.sendBeacon("http://127.0.0.1:9000/hub/api/info", "");
});
$(document).ready(function(){
  if(is_exercise == "True" && can_skip == "False"){
      setTimeout(function() {show_solution();}, delay_time*1000);
  }
  // Codemirror object, language modes and initial content
  // Get the textarea node

  var textarea_node = document.querySelector('#answer');

  var mode_dict = {
    'python': 'python',
    'c': 'text/x-csrc',
    'cpp': 'text/x-c++src',
    'java': 'text/x-java',
    'bash': 'text/x-sh',
    'scilab': 'text/x-csrc',
    'r':'text/x-rsrc',
  }

  // Websocket to connect to Django Websocket
  if(question_type === "code") {
    Socket = new WebSocket(
      ws_scheme + window.location.host + '/ws/quiz'
    );
    Socket.onmessage = function(e) {
      unlock_screen();
      const data = JSON.parse(e.data);
      console.log(data.success)
      var error_output = document.getElementById("error_panel");
      error_output.innerHTML = data.response;
      focus_on_error(error_output);
    };

    Socket.onclose = function(e) {
      unlock_screen();
      console.error('Chat socket closed unexpectedly');
    };
  }

  // Code mirror Options
  var options = {
      mode: mode_dict[lang],
      gutter: true,
      lineNumbers: true,
      styleSelectedText: true,
      onChange: function (instance, changes) {
          render();
      }
  };
  if (question_type == 'code'){
  
  // Initialize the codemirror editor
  global_editor.editor = CodeMirror.fromTextArea(textarea_node, options);
  // Setting code editors initial content
  global_editor.editor.setValue(init_val);
}
if (question_type == 'upload' || question_type == 'code') {
  $('#code').submit(function(e) {
    lock_screen();
    if (question_type == "code"){
    var data = $(this).serializeArray();
  }
  else if (question_type == "upload"){
    var data = new FormData(document.getElementById("code"));
  }
    ajax_check_code($(this).attr("action"), "POST", "html", data, null)
    // Socket.send(JSON.stringify({'message': data, 'kernel_id': kernel_id}));
    e.preventDefault(); // To stop the default form submission.
  });
  }

  reset_editor = function() {
      global_editor.editor.setValue(init_val);
      global_editor.editor.clearHistory();
      $('#undo_changes').modal('hide');
  }

  confirm = function(){
    $("#undo_changes").modal("show");
  }
});
function user_arranged_options(){
    var temp_array = []
    var add_array = document.getElementById("arrange_order");
    var ans_array = order_array.children().get()
                      var answer_is = $.each(ans_array, function( index, value ) {
                      temp_array.push(value.id);
                      });
    add_array.value = temp_array
}
