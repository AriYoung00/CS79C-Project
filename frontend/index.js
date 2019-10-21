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

function createCookie(name, value, days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        var expires = "; expires=" + date.toGMTString();
    }
    else var expires = "";

    document.cookie = name + "=" + value + expires + "; path=/";
}

function eraseCookie(name) {
    createCookie(name, "", -1);
}

$(document).ready(function(e) {
    console.log("asss");
    let user_id = readCookie("whimsy-user_id");
    let token = readCookie("whimsy-token");

    console.log(user_id);
    console.log(token);

    if (user_id == null || token == null) {
        eraseCookie("whimsy-user_id");
        eraseCookie("whimsy-token");

        window.location.replace("login.html");
    }

    console.log("boutta start ajax");
    $.ajax({
        type: "POST",
        url: "https://kz7wbbbpe1.execute-api.us-west-1.amazonaws.com/Production/user/verify",
        data: JSON.stringify({"user_id": user_id, "token": token}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        crossDomain: true,
        success: function (data) {
            // if (!data.success) {
            //     eraseCookie("whimsy-user_id");
            //     eraseCookie("whimsy-token");
            //
            //     window.location.replace("login.html");
            // }

            userID = user_id;
            userToken = token;

            console.log(user_id);
            console.log(token);

            console.log("ajax success");

            $.ajax({
                type: "POST",
                url: "https://kz7wbbbpe1.execute-api.us-west-1.amazonaws.com/Production/post/get",
                data: JSON.stringify({"user_id": user_id, "token": token}),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                crossDomain: true,
                success: function (data) {
                    if (!data.success)
                        return;

                    $("#post-title").html(data.title);
                    $("#post-body").html(data.body).show();
                    $("#score").html(data.score).show();
                    currendUPID = data.upid;
                    currentVote = 0;

                    $("#next-btn").show();
                    $("#upvote-btn").show();
                    $("#downvote-btn").show();
            }
    });
        }
    });
});

$("#next-btn").on("click.simple", function (e) {
    $.ajax({
        type: "POST",
        url: "https://kz7wbbbpe1.execute-api.us-west-1.amazonaws.com/Production/post/get",
        data: JSON.stringify({"user_id": user_id, "token": token}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        crossDomain: true,
        success: function (data) {
            if (!data.success)
                return;

            $("#post-title").html(data.title);
            $("#post-title").html(data.title);
            $("#post-body").html(data.body).show();
            $("#score").html(data.score).show();
            currendUPID = data.upid;
            currentVote = 0;

            $("#next-btn").show();
            $("#upvote-btn").show();
            $("#downvote-btn").show();
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
    var s = $("score");
    let old_score = s.html();
    s.html(old_score + scoreDelta);


    $.ajax({
        type: "POST",
        url: "https://kz7wbbbpe1.execute-api.us-west-1.amazonaws.com/Production/post/vote",
        data: JSON.stringify({"user_id": userID, "token": userToken, "upid": currendUPID, "vote_type": voteType}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {

        }
    });
}


$("#upvote-btn").on("click", function (e) {
    castVote(true);
});

$("#downvote-btn").on("click", function(e) {
    castVote(false);
});