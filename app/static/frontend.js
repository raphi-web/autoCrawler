$(document).ready(function() {
    console.log("doc_ready!");
    var socket = io();

    socket.on('connect', function() {
        socket.emit('connection', { data: 'I\'m connected!' });
    });

    socket.on('my_response', function(msg, cb) {
        console.log("Got Message from server!");
        $('#log').append('<br>' + $('<div/>').text(msg.data).html());
    });

    socket.on('start_collecting', function() {
        $('#clear').removeClass("is-disabled").addClass("is-link");
        $('#gpkg').removeClass("is-disabled").addClass("is-link");

    });


    socket.on('finished_collecting', function() {
        $('#log').text("DONE Collecting!");

    });


    socket.on("download_ready", function() {
        window.location = 'http://127.0.0.1:5000/get-files/booking_data.gpkg';
    })

    $('#clear').on("click", function() {
        let isactive = true;
        let classList = document.getElementById('clear').className.split(/\s+/);
        for (let i = 0; i < classList.length; i++) {
            if (classList[i] === "is-disabled") {
                isactive = false;
            }
        }
        if (isactive) {
            $('#log').text("");
            socket.emit("clear", { data: 'clear' });
            $('#clear').removeClass("is-link");

        }
    });

    $('#gpkg').on("click", function() {
        let isactive = true;
        let classList = document.getElementById('gpkg').className.split(/\s+/);
        for (let i = 0; i < classList.length; i++) {
            if (classList[i] === "is-disabled") {
                isactive = false;
            }
        }
        if (isactive) {
            $('#log').text("").text("Processing Data, this can take a while...");
            socket.emit("gpkg", { data: 'gpkg' });
            $('#clear').removeClass("is-link");
            $('#gpkg').removeClass("is-link");
        }
    });

});