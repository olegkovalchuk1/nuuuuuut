const links = document.querySelectorAll(".menu-link");

links.forEach(link => {
    link.addEventListener("click", function(){

        links.forEach(l => l.classList.remove("active"));

        this.classList.add("active");

    });
});

function togglePassword() {
    const password = document.getElementById("password");

    if (password.type === "password") {
        password.type = "text";
    } else {
        password.type = "password";
    }
}


document.addEventListener("DOMContentLoaded", function () {

    const buttons = document.querySelectorAll("button");

    buttons.forEach(function(button){

        button.addEventListener("mousedown", function(){
            button.style.filter = "brightness(80%)";
        });

        button.addEventListener("mouseup", function(){
            button.style.filter = "brightness(100%)";
        });

        button.addEventListener("mouseleave", function(){
            button.style.filter = "brightness(100%)";
        });

    });

});