from flask import Flask, request, render_template, redirect, session, url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import random

app = Flask(__name__)
socketio = SocketIO(app)
app.config["SECRET_KEY"] = "randomsecretkey"

rooms = {}

def generate_unique_code(n):
    while True:
        code = ""
        for i in range(n):
            code += random.choice("ABCDEFGHIJKLMNOPQRSTUVXYZW")

        if code not in rooms:
            break

    return code


@app.route("/", methods=["GET", "POST"])
def index():
    session.clear()
    if request.method == "POST":
        username = request.form.get("name")
        room_code = request.form.get("room-code")
        create = request.form.get("create-btn")
        join = request.form.get("join-btn")

        if join is not None:
            if not username or not room_code:
                error_mess = "Must provide name AND room code to join an existing room"
                return render_template("index.html", error_mess=error_mess)
            

        elif create is not None:
            if not username:
                error_mess = "Must provide name to create a room"
                return render_template("index.html", error_mess=error_mess)
            
            room_code = generate_unique_code(4)
            rooms[room_code] = {"members": 0, "messages": []}

        elif room_code not in rooms:
            error_mess = "Room does not exist."
            return render_template("index.html", error_mess=error_mess)

        session["room"] = room_code
        session["name"] = username
        return redirect(url_for("room"))
        

    return render_template("index.html")



@app.route("/room", methods=["GET", "POST"])
def room():
    room_code = session["room"]
    if room_code is None or session.get("name") is None or room_code not in rooms:
        return redirect(url_for("index"))

    return render_template("room.html", code=room_code, messages=rooms[room_code]["messages"])



@socketio.on("message")
def message(data):
    room_code = session.get("room")
    if room_code not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room_code)
    rooms[room_code]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room_code = session.get("room")
    name = session.get("name")
    if not room_code or not name:
        return
    if room_code not in rooms:
        leave_room(room_code)
        return
    
    join_room(room_code)
    send({"name": name, "message": "has entered the room"}, to=room_code)
    rooms[room_code]["members"] += 1
    print(f"{name} joined {room_code}")


@socketio.on("disconnect")
def disconnect():
    room_code = session.get("room")
    name = session.get("name")
    leave_room(room_code)
    
    if room_code in rooms:
        rooms[room_code]["members"] -= 1
        if rooms[room_code]["members"] <= 0:
            del rooms[room_code]

    send({"name": name, "message": "has left the room"}, to=room_code)
    print(f"{name} has left the {room_code}")


if __name__ == "__main__":
    socketio.run(app, debug=True)
