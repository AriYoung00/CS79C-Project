import jQuery from "jquery";

var currendUPID = null;
var currentVote = 0;
var userID = null;
var userToken = null;

// Cookies - thank you, stack overflow
function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function eraseCookie(name) {
    createCookie(name, "", -1);
}

$(document).on("ready", function(e) {
    let user_id = readCookie("whimsy-user_id");
    let token = readCookie("whimsy-token");

    if (user_id == null || token == null) {
        eraseCookie("whimsy-user_id");
        eraseCookie("whimsy-token");

        window.location.replace("login.html");
    }

    $.ajax({
        type: "POST",
        url: "https://kz7wbbbpe1.execute-api.us-west-1.amazonaws.com/Production/user/verify",
        data: JSON.stringify({"user_id": user_id, "token": token}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            if (!data.success) {
                eraseCookie("whimsy-user_id");
                eraseCookie("whimsy-token");

                window.location.replace("login.html");
            }

            userID = user_id;
            userToken = token;
        }
    });
});

$("#next-btn").on("click", function (e) {
    $.ajax({
        type: "POST",
        url: "https://kz7wbbbpe1.execute-api.us-west-1.amazonaws.com/Production/post/get",
        data: JSON.stringify({"user_id": user_id, "token": token}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            if (!data.success)
                return;

            $("#post-title").html(data.title);
            $("#post-body").html(data.post_body);
            currendUPID = data.upid;
            currentVote = 0;
        }
    });
});

function castVote(voteType) {
    var scoreDelta = 0;
    if (currentVote == 1 && voteType)
        scoreDelta = -1;
    else if (currentVote == -1 && voteType)
        scoreDelta = 2;
    else if (currentVote == 1 && !voteType)
        scoreDelta = -2;
    else if (currentVote == -1 && !voteType)
        scoreDelta = 1;

    currentVote = voteType ? 1 : -1;


    $.ajax({
        type: "POST",
        url: "https://kz7wbbbpe1.execute-api.us-west-1.amazonaws.com/Production/post/vote",
        data: JSON.stringify({"user_id": userID, "token": userToken, "upid": currendUPID, "vote_type": voteType}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            var s = $("score");
            let old_score = s.text();
            s.html(old_score + scoreDelta);
        }
    });
}


$("#upvote-btn").on("click", function (e) {
    castVote(true);
});

$("#downvote-btn").on("click", function(e) {
    castVote(false);
});