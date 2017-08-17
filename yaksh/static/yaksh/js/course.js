$(document).ready(function(){
$(".checkall").change( function(){
        if($(this).prop("checked")) {
                $("#enroll-all input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#enroll-all input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });
$(".enroll").change( function(){
        if($(this).prop("checked")) {
                $("#enroll input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#enroll input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });
$(".reject").change( function(){
        if($(this).prop("checked")) {
                $("#reject input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#reject input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });

$(function() {
    $('textarea#email_body').froalaEditor({
        heightMin: 100,
        heightMax: 200
    })
  });

$("#send_mail").click(function(){
    var subject = $("#subject").val();
    var body = $('#email_body').val();
    var status;
    if (subject == '' || body == ''){
        status = false;
        $("#error_msg").html("Please enter mail details");
        $("#dialog").dialog();
    }
    else{
        status = true;
    }
    return status;
});

$('#send_mail_form').submit(function(eventObj) {
    var selected = [];
    $('#reject input:checked').each(function() {
        selected.push($(this).attr('value'));
    });
    if(selected.length > 0) {
        return true;
    }
    else {
        $("#error_msg").html("Please select atleast one user");
        $( "#dialog" ).dialog();
        return false;
    }
});

});
