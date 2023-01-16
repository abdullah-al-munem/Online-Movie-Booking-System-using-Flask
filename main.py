from flask import Flask, request, render_template, redirect, session
from flask_mail import Mail, Message
import json
app = Flask(__name__)
app.secret_key = 'super secret key'

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'tmpmsg03@gmail.com'
app.config['MAIL_PASSWORD'] = 'tmpcse479'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

from copy import deepcopy
from datetime import datetime
from bson.objectid import ObjectId
from operator import itemgetter

import pymongo
db_client = pymongo.MongoClient("mongodb://localhost:27017")
db = db_client["movie_theater"]
user_info = db["user"]
movie_info = db["movie"]
screening_info = db["screening"]

"""Current location selected for theater is stored in this variable."""
cur_location = "Aftab Nagar"


SEAT_BOOKED = {chr(ord('A') + i) : {j : None for j in range(1,19)}  for i in range(12)} #Structure of the seats of a Hall

def cust_date_str_t_str(date):
    date = datetime.strptime(date, "%Y-%m-%d").date()
    return date.strftime("%#d") + ' ' + date.strftime("%b") + ' ' + date.strftime("%Y")

def cust_time_str_t_str(time):
    time = datetime.strptime(time,"%H:%M").time()
    return time.strftime("%#I") + ':' + time.strftime("%M") + ' ' + time.strftime("%p").lower()

@app.route('/addmovie', methods=['GET', "POST"])
def addmovie():
    if request.method == "POST":
        form = dict(request.form)
        form['rating'] = int(form['rating'])
        movie_info.insert_one(form)
        return ""
    #return render_template("addmovie.html", **locals())
    return ""


@app.route('/deletemovie', methods=['GET', "POST"])
def deletemovie():
    if request.method == "POST":
        movie_id = request.form.get('movie_id', None)
        movie_info.delete_one({"_id" : ObjectId(movie_id)})
        screening_info.delete_many({"movie_id" : movie_id})
    return ""


@app.route('/updatemovie', methods=['GET', "POST"])
def updatemovie():
    if request.method == "POST":
        form = dict(request.form)
        movie_id = form["_id"]
        del form["_id"]
        form['rating'] = int(form['rating'])
        movie_info.replace_one({"_id":ObjectId(movie_id)},form)
        movie = movie_info.find_one({"_id":ObjectId(movie_id)})
        return ""

    movie_id = request.args.get('movie_id', None)
    movie = movie_info.find_one({"_id":ObjectId(movie_id)})
    #return render_template("updatemovie.html", **locals())
    return ""


@app.route('/addscreening', methods=['GET', "POST"])
def addscreening():
    if request.method == "POST":
        exists = None

        form = dict(request.form)
        #form["movie_id"] = ObjectId(form["movie_id"])

        screening = deepcopy(form)
        del screening["movie_id"]

        if screening_info.find_one(screening) is None:
            form['seats'] = json.dumps(SEAT_BOOKED)
            screening_info.insert_one(form)
            exists = False
        else:
            exists = True
        return str(exists)
    movies = list(movie_info.find())
    #return render_template("addscreening.html", **locals())
    return ""


@app.route('/updatescreening', methods=['GET', "POST"])
def updatescreening():
    if request.method == "POST":
        form = dict(request.form)
        form["_id"] = ObjectId(form["_id"])

        screening_id = form["_id"]

        screening = screening_info.find_one({"_id":screening_id})

        form["seats"] = screening["seats"]

        if(form == screening):
            return "True"
        del form["_id"]
        del form["seats"]

        print(screening_info.find_one(form))
        if screening_info.find_one(form):
            return "False"

        form["seats"] = screening["seats"]
        screening_info.replace_one({"_id":screening_id},form)
        screening = screening_info.find_one({"_id":screening_id})
        return "True"

    movies = list(movie_info.find())
    screening_id = request.args.get('screening_id', None)
    screening = screening_info.find_one({"_id":ObjectId(screening_id)})
    #print(screening_id)
    #print(screening)
    #return render_template("updatescreening.html", **locals())
    return ""


@app.route('/deletescreening', methods=['GET', "POST"])
def deletescreening():
    if request.method == "POST":
        screening_id = request.form.get('screening_id', None)
        screening_info.delete_one({"_id" : ObjectId(screening_id)})
    return ""

@app.route('/movielist', methods=['GET', "POST"])
def movielist():
    movies = list(movie_info.find())
    #return render_template("movielist.html", **locals())
    return ""

@app.route('/screeninglist', methods=['GET', "POST"])
def screeninglist():
    movies = list(movie_info.find())
    screenings = list(screening_info.find())
    #return render_template("screeninglist.html", **locals())
    return ""

@app.route('/adminpanel', methods=['GET', "POST"])
def adminpanel():
    global session
    movies = list(movie_info.find())
    screenings = list(screening_info.find())

    return render_template("adminpanel.html", **locals())

@app.route('/moviebook', methods=['GET', "POST"])
def moviebook():

    if "logged_in" not in session:
        return redirect("/login")
    global cur_location

    if request.method == "POST":
        form = dict(request.form)
        print(form)

        selected_hall = form['selectedHall']
        seats = json.loads(form['selectedSeats'])
        movie_id = form['movie_id']
        get_date = form['date']
        get_time = form['time']

        screening = screening_info.find_one({"movie_id": movie_id, "location": cur_location, "date": get_date, "time": get_time, "hall": selected_hall})
        current_seats = screening['seats']
        current_seats = json.loads(current_seats)

        can_purchase = True
        for seat in seats:
            seat = seat.split("-")
            can_purchase = can_purchase and (current_seats[seat[1]][seat[2]] is None)
            current_seats[seat[1]][seat[2]] = session["user_id"]
            # current_seats[seat[1]][seat[2]] = 1

        if can_purchase:
            screening['seats'] = json.dumps(current_seats)
            screening_info.replace_one({"movie_id": movie_id, "location": cur_location, "date": get_date, "time": get_time, "hall": selected_hall}, screening)

        print(can_purchase)
        return str(can_purchase)

    movie_id = request.args.get('movie_id', None)
    get_date = request.args.get('date', None)
    get_time = request.args.get('time', None)

    hall_seats = {}
    halls = []
    for screening in screening_info.find({"movie_id": movie_id, "location": cur_location, "date": get_date, "time": get_time}):
        halls.append(screening['hall'])
        hall_seats[screening['hall']] = json.loads(screening['seats'])
    halls.sort()

    movie = movie_info.find_one({"_id":ObjectId(movie_id)})

    date = cust_date_str_t_str(get_date)
    time = cust_time_str_t_str(get_time)

    return render_template("moviebook.html", **locals(), **globals())

def filtershowtime(filter_form):
    #print(filter_form)
    if filter_form and "movie_id" not in filter_form:
        categories = json.loads(filter_form.get('categories', None))
        genres = json.loads(filter_form.get('genres', None))
        languages = json.loads(filter_form.get('languages', None))
        weekdays_form = json.loads(filter_form.get('weekdays', None))
        rating = json.loads(filter_form.get('rating', None))

    global cur_location
    shows = {}
    weekday, month_name, only_date = {}, {}, {}

    dates = []
    movie_info_by_id = {}
    formatted_time = {}

    for screening in screening_info.find({"location":cur_location}):
        movie = movie_info.find_one({"_id":ObjectId(screening['movie_id'])})
        if "movie_id" in filter_form and filter_form['movie_id'] != str(movie['_id']):
            continue

        date = datetime.strptime(screening['date'],"%Y-%m-%d").date()

        time = screening['time']
        formatted_time[time] = cust_time_str_t_str(time)

        weekday[date] = date.strftime("%a")
        month_name[date] = date.strftime("%b")
        only_date[date] = date.strftime("%#d")

        movie['release'] = cust_date_str_t_str(movie['release'])
        movie_info_by_id[movie['_id']] = movie

        if filter_form and "movie_id" not in filter_form:
            category_ok = False
            for category in categories:
                category_ok = category_ok or (category in movie["category"])

            genre_ok = False
            for genre in genres:
                genre_ok = genre_ok or (genre in movie["genre"])

            language_ok = False
            for language in languages:
                language_ok = language_ok or (language in movie["language"])

            weekday_ok = False
            for weekday_form in weekdays_form:
                weekday_ok = weekday_ok or (weekday_form == weekday[date])

            rating_ok = rating[0] <= movie["rating"] and movie["rating"] <= rating[1]

            if not category_ok or not genre_ok or not language_ok or not weekday_ok or not rating_ok:
                continue

        if date not in shows:
            shows[date] = {}
        if movie['_id'] not in shows[date]:
            shows[date][movie['_id']] = []

        shows[date][movie['_id']].append(time)

    for date in shows:
        for movie_id in shows[date]:
            shows[date][movie_id] = list(set(shows[date][movie_id]))
            shows[date][movie_id].sort()

    for date in shows:
        dates.append(date)
    dates.sort()
    return shows,weekday, month_name, only_date,dates,movie_info_by_id,formatted_time


@app.route('/showtime', methods=['GET', "POST"])
def showtime():
    global filter_form
    if request.method == "POST":
        filter_form = dict(request.form)
        print(request.form)
        print(filter_form)
        shows, weekday, month_name, only_date, dates, movie_info_by_id, formatted_time = filtershowtime(filter_form)
        ret = render_template("showtime-filtered-section-only.html", **locals(), **globals())
        ret = ret.split("\n", 28)[28]
        ret = "\n".join(ret.split("\n")[:-3])
        print(ret)
        return ret

    shows, weekday, month_name, only_date, dates, movie_info_by_id, formatted_time = filtershowtime({})
    return render_template("showtime.html", **locals(), **globals())

@app.route('/search/', methods=['GET', "POST"])
def search():
    query = request.form.get('search')
    # print(query)
    s_query = query.lower()
    movie_info_by_id = []

    for movie in movie_info.find():
        movie['release'] = cust_date_str_t_str(movie['release'])
        if s_query in movie['title'].lower():
            movie_info_by_id.append(movie)
        # print(movie)
        # movie_info_by_id.append(movie)

    movie_info_by_id_sorted = sorted(movie_info_by_id, key=itemgetter('release'))


    return render_template("search.html", **locals())

@app.route('/movies/<string:id>', methods=['GET', "POST"])
def movies(id):
    global cur_location
    tmp = cur_location
    showing = True
    movie_info_by_id = []

    for screening in screening_info.find({"location": cur_location}):
        movie = movie_info.find_one({"_id": ObjectId(screening['movie_id'])})

        movie['release'] = cust_date_str_t_str(movie['release'])
        # print(movie)
        if movie not in movie_info_by_id:
            movie_info_by_id.append(movie)
        # movie_info_by_id.append(movie)

    movie_info_by_id_sorted = sorted(movie_info_by_id, key=itemgetter('release'))
    total_movie = len(movie_info_by_id_sorted)
    # print(total_movie, movie_info_by_id_sorted)

    movie_info_by_id_2 = []

    for movie in movie_info.find():
        movie['release'] = cust_date_str_t_str(movie['release'])
        # print(movie)
        if movie not in movie_info_by_id_2:
            movie_info_by_id_2.append(movie)
        # movie_info_by_id_2.append(movie)

    movie_info_by_id_2_sorted = sorted(movie_info_by_id_2, key=itemgetter('release'))
    # movie_info_by_id_2_sorted = [x for x in movie_info_by_id_2_sorted if x not in movie_info_by_id_sorted]
    total_movie_2 = len(movie_info_by_id_2)
    print(total_movie_2, movie_info_by_id_2_sorted)

    final_list = []
    for x in movie_info_by_id_2_sorted:
        if x not in movie_info_by_id_sorted:
            final_list.append(x)
    total_movie_2 = len(final_list)
    print(total_movie_2, final_list)

    if id == "1":
        return render_template("movies.html", **locals())
    elif id == "2":
        return render_template("movies.html", **locals())
    else:
        single_movie = movie_info.find_one({"_id": ObjectId(id)})

        single_movie['release'] = cust_date_str_t_str(single_movie['release'])
        return render_template("moviedescription.html", **locals())
    return ""

@app.route('/ticket_price', methods=['GET', "POST"])
def ticket_price():
    tmp = cur_location
    return render_template("ticket_price.html", **locals())

@app.route('/news', methods=['GET', "POST"])
def news():
    tmp = cur_location

    return render_template("news.html", **locals())

@app.route('/about_us', methods=['GET', "POST"])
def about_us():
    tmp = cur_location
    return render_template("about_us.html", **locals())

@app.route('/contact_us', methods=['GET', "POST"])
def contact_us():
    tmp = cur_location
    if request.method == 'POST':
        msg = Message('Hello from the other side!', sender='tmp@tmp.io', recipients=['tmpmsg03@gmail.com'])
        msg.body = "Hey Paul, sending you this email from my Flask app, lmk if it works"
        # mail.send(msg)
        # print(msg.body)

    return render_template("contact_us.html", **locals())

@app.route('/', methods=['GET', "POST"])
def index():
    global cur_location
    if request.method == "POST":
        cur_location = request.form['hall']
        print(cur_location)
    showing = True
    movie_info_by_id = []
    tmp = cur_location

    for screening in screening_info.find({"location": cur_location}):
        movie = movie_info.find_one({"_id": ObjectId(screening['movie_id'])})

        movie['release'] = cust_date_str_t_str(movie['release'])
        # print(movie)
        if movie not in movie_info_by_id:
            movie_info_by_id.append(movie)

    # movie_info_by_id = list(set(movie_info_by_id))
    movie_info_by_id_sorted = sorted(movie_info_by_id, key=itemgetter('release'), reverse=True)
    total_movie = len(movie_info_by_id_sorted)
    print(total_movie, movie_info_by_id_sorted)

    movie_info_by_id_2 = []

    for movie in movie_info.find():
        movie['release'] = cust_date_str_t_str(movie['release'])
        # print(movie)
        if movie not in movie_info_by_id_2:
            movie_info_by_id_2.append(movie)

    # movie_info_by_id_2 = list(set(movie_info_by_id_2))
    movie_info_by_id_2_sorted = sorted(movie_info_by_id_2, key=itemgetter('release'), reverse=True)
    # movie_info_by_id_2_sorted = [x for x in movie_info_by_id_2_sorted if x not in movie_info_by_id_sorted]
    total_movie_2 = len(movie_info_by_id_2)
    # print(total_movie_2, movie_info_by_id_2_sorted)

    final_list = []
    for x in movie_info_by_id_2_sorted:
        if x not in movie_info_by_id_sorted:
            final_list.append(x)
    total_movie_2 = len(final_list)
    print(total_movie_2, final_list)
    # if request.method == "POST":
    #     flg = int(request.form['flg'])
    #     if flg == 1:
    #         showing = True
    #     if flg == 2:
    #         showing = False

    return render_template("index.html", **locals())




@app.route('/reset', methods=['GET', "POST"])
def reset():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        msg = ""

        if user_info.find_one({"email": email} or {"phone": email}):
            if len(password) > 7:
                db.changeUserPassword(email, password)
                msg = "success"
                return msg
            else:
                msg = "short"
                return msg
        else:
            msg = "wronguser"
            return msg

    return render_template("resetPassword.html", **locals())


@app.route('/login', methods=['GET', "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        msg = ""

        if user_info.find_one({"email": email}) or user_info.find_one({"phone": email}):
            if user_info.find_one({"password": password}):
                msg = "success"
                session["logged_in"] = True

                if user_info.find_one({"email": email}):
                    session["email"] = email
                    session["user_id"] = str(user_info.find_one({"email": email})["_id"])

                if user_info.find_one({"phone": email}):
                    session["phone"] = email
                    session["user_id"] = str(user_info.find_one({"email": email})["_id"])
                return msg

            else:
                msg = "wrongpass"
                return msg

        else:
            msg = "wronguser"
            return msg

    if "logged_in" in session:
        return redirect ("/")

    return render_template("login.html", **locals())

@app.route('/logout', methods=['GET', "POST"])
def logout():
    session.clear()
    return redirect("/login")

@app.route('/register', methods=['GET', "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        conf_password = request.form["conf_password"]
        msg = ""

        if user_info.find_one({"email": email}):
            msg = "emailexist"
            return msg

        if len(phone) == 11 and phone[0] == "0" and phone[1] == "1":
            if user_info.find_one({"phone": phone}):
                msg = "phoneexist"
                return msg
        else:
            msg = "phoneinv"
            return msg

        if len(password) > 7:
            if password == conf_password:
                user_info.insert_one({"fullname": fullname, "email": email, "phone": phone, "password": password, "role": "user"})
                msg = "success"
                return msg
            else:
                msg = "wrongpass"
                return msg
        else:
            msg = "short"
            return msg

    return render_template("registration.html", **locals())


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
