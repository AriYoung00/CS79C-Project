// Cookies - thank you, stack overflow
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

$("#login-submit").on("click", function (e) {
    var email = $("#email").val();
    var passwd = $("#password").val();

    $.ajax({
        type: "POST",
        url: "https://kz7wbbbpe1.execute-api.us-west-1.amazonaws.com/Production/user/login",
        data: JSON.stringify({"email": email, "password": passwd}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        crossDomain: true,
        success: function (data) {
            if (!data.success) {
                $("#fail-alert-login").show();
            }

            createCookie("whimsy-user_id", data.user_id, 7);
            createCookie("whimsy-token", data.token, 7);

            console.log(data);
            alert("pause3");

            window.location.replace("index.html");
        }
    });
});

$("#signup-submit").on("click", function (e) {
    var email = $("#email").val();
    var passwd = $("#password").val();

    console.log(email);
    console.log(passwd);

    $.ajax({
        type: "POST",
        url: "https://kz7wbbbpe1.execute-api.us-west-1.amazonaws.com/Production/user/create",
        data: JSON.stringify({"email": email, "password": passwd}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        crossDomain: true,
        success: function (data) {
            if (!data.success) {
                $("#fail-alert-signup").show();
            }

            createCookie("whimsy-user_id", data.user_id, 7);
            createCookie("whimsy-token", data.token, 7);


            window.location.replace("index.html");
        }
    });
});