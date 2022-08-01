from xml.dom.minidom import CharacterData
from flask import Flask, redirect,render_template,request,url_for,session,logging,flash
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


# Kullanıcı Giriş Decaratorü
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else: 
            flash("Bu sayfayı görmek için lütfen giriş yapın", "danger")
            return redirect(url_for("login"))
    return decorated_function



# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 4,max = 25)])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 35)])
    email = StringField("Email Adresi",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Girin...")])
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message = "Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor...")
    ])
    confirm = PasswordField("Parola Doğrula")

# Kullanıcı Giriş Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 35)])
    password = PasswordField("Parola:")

# Nick Ekleme 
class NickForm(Form):
    server = StringField("Sunucu ismi")
    nick = StringField ("Karakter isimleri",validators=[validators.Length(min = 5,max = 35)])

class SearchNick(Form):
    server = StringField("Sunucu ismi")
    nick = StringField ("Karakter isimleri",validators=[validators.Length(min = 5,max = 35)])

app = Flask(__name__)
app.secret_key="whoseitem"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "whoseitem"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)



@app.route("/")

def index():

    return render_template("index.html")  



@app.route("/layout")

def layout():

    return render_template("layout.html")

@app.route("/about")

def about():

    return render_template("about.html")

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From nicks where author = %s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        mylist=cursor.fetchall()
        return render_template("dashboard.html",mylist=mylist)
    else: 
        return render_template("dashboard.html")
@app.route("/addnick",methods=["GET","POST"])
@login_required
def addnick():
    form= NickForm(request.form)
    if request.method == "POST" and form.validate():
        server = form.server.data
        nicks = form.nick.data
        
        cursor = mysql.connection.cursor()
        sorgu = "Insert into nicks(title,author,content)    VALUES (%s,%s,%s )"
        
        cursor.execute(sorgu,(server,session["username"],nicks))
        mysql.connection.commit()
        cursor.close()
        flash("Nickler Başarıyla eklendi","success")
        return redirect(url_for("dashboard"))
    
    return render_template("addnick.html",form=form)

@app.route("/register",methods=["GET","POST"])

def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username= form.username.data
        email= form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)
    
@app.route("/login",methods=["GET","POST"])

def login():
    form = LoginForm(request.form)

    if request.method == "POST" and form.validate():

        username= form.username.data
        password_enterred = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * from users where username = %s "
        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_enterred,real_password):
                flash("giriş başarılı","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else :
                flash("şifre hatalı","danger")
                return redirect(url_for("login"))
        
        else : 
            flash("Böyle bir kullanıcı yok","danger")
            return redirect(url_for("login"))

    else:
        return render_template("login.html",form=form)

@app.route("/logout")

def logout():

    session.clear()
    flash("çıkış yapıldı","success")
    return redirect(url_for("index"))


@app.route("/nicks",methods=["GET","POST"])

def nicks():

    cursor = mysql.connection.cursor()

    sorgu = "Select * From nicks"

    result = cursor.execute(sorgu)

    if result > 0   :
        
        nicks = cursor.fetchall()
        return render_template("nicks.html",nicks=nicks)
    else :
        
        return render_template("nicks.html")

@app.route("/nick/<string:id>")

def nick(id):
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * from nicks where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        nick = cursor.fetchone()
        return render_template("nick.html",nick = nick)
    else:
        return render_template("nick.html")

#nick silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from nicks where author = %s and id = %s"
    result= cursor.execute(sorgu,(session["username"],id))
    
    if result >0:
        sorgu2 = "Delete from nicks where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("böyle bir makale yok veya bu işleme yetkiniz yok","danger")
        return redirect(url_for("index"))
        
#nick editleme
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def edit(id):
   if request.method == "GET":
       cursor = mysql.connection.cursor()

       sorgu = "Select * from nicks where id = %s and author = %s"
       result = cursor.execute(sorgu,(id,session["username"]))

       if result == 0:
           flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
           return redirect(url_for("index"))
       else:
           veri = cursor.fetchone()
           form = NickForm()

           form.server.data = veri["title"]
           form.nick.data = veri["content"]
           return render_template("edit.html",form = form)

   else:
    
      # POST REQUEST
       form = NickForm(request.form)

       newNick = form.server.data
       newServer = form.nick.data

       sorgu2 = "Update nicks Set title = %s,content = %s where id = %s "

       cursor = mysql.connection.cursor()

       cursor.execute(sorgu2,(newNick,newServer,id))

       mysql.connection.commit()

       flash("Nick başarıyla güncellendi","success")

       return redirect(url_for("dashboard"))
# Arama URL
@app.route("/search",methods = ["GET","POST"])
def search():
   if request.method == "GET":
       return redirect(url_for("index"))
   else:
       keyword = request.form.get("keyword")

       cursor = mysql.connection.cursor()

       sorgu = "Select * from nicks where content like '%" + keyword +"%'"

       result = cursor.execute(sorgu)

       if result == 0:
           flash("Aranan kelimeye uygun nick bulunamadı...","warning")
           return redirect(url_for("nicks"))
       else:
           nicks = cursor.fetchall()

           return render_template("nicks.html",nicks = nicks)


@app.route("/users/<string:id>")

def users(id):
    return "Users İd:" + id



if __name__ == "__main__":
    app.run(debug=True)